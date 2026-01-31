import duckdb
import numpy as np
from pathlib import Path

import re

from loguru import logger
from mircat_v2.configs import read_dbase_config, write_config

# Path to the DuckDB schema file
dbase_schema_file = Path(__file__).parent / "configs" / "dbase_duckdb.sql"


def add_dbase_subparser(subparsers):
    """Add database management subcommands to the CLI."""
    dbase_parser = subparsers.add_parser(
        "dbase",
        help="Database management commands",
        description="mircat-v2 database management commands.",
    )
    dbase_subparsers = dbase_parser.add_subparsers(
        dest="dbase_command", description="Database operations:"
    )

    # Create a new database
    create_parser = dbase_subparsers.add_parser("create", help="Create a new database")
    create_parser.add_argument(
        "dbase_path",
        type=Path,
        help="Path to the database file",
    )
    create_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the database if it already exists",
    )

    # Set an existing database
    set_parser = dbase_subparsers.add_parser(
        "set", help="Set an existing DuckDB database file to be used in mircat-v2"
    )
    set_parser.add_argument(
        "dbase_path", type=Path, help="Path to the existing database file."
    )
    set_parser.add_argument(
        "--create-if-missing",
        "-c",
        action="store_true",
        help="Create the database if it does not exist.",
    )

    # Update an existing database schema
    update_parser = dbase_subparsers.add_parser(
        "update",
        help="Update an existing database schema to match the current mircat-v2 schema",
    )
    update_parser.add_argument(
        "dbase_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the database file. If not provided, uses the configured database.",
    )


def run_dbase_command(args) -> None:
    """Run the appropriate function depending on the given dbase command."""
    match args.dbase_command:
        case "create":
            create_database(args.dbase_path, args.overwrite)
        case "set":
            set_database(args.dbase_path, args.create_if_missing)
        case "update":
            update_database(args.dbase_path)
        case _:
            logger.error(f"Unknown dbase command: {args.dbase_command}")


def create_database(dbase_path: Path, overwrite: bool = False) -> None:
    """Create a new DuckDB database at the specified path.

    Parameters
    ----------
    dbase_path : Path
        Path to the database file.
    overwrite : bool
        If True, overwrite the database if it already exists.
    """
    if dbase_path.exists() and not overwrite:
        raise FileExistsError(
            f"Database file {dbase_path} already exists. Use `mircat-v2 dbase set` to use it or `--overwrite` to completely overwrite."
        )
    elif dbase_path.exists() and overwrite:
        response = input(
            "Are you sure you want to overwrite the existing database? This will not copy data to the new one. (y/n): "
        )
        if response.lower() != "y":
            logger.info(f"Left existing database at {dbase_path} intact.")
            return
        logger.info(f"Overwriting existing database at {dbase_path}")
        dbase_path.unlink()

    conn = duckdb.connect(str(dbase_path))
    _create_tables_from_schema(conn)
    conn.close()
    logger.success(f"Database created at {dbase_path}")
    _save_dbase_path(dbase_path)


def set_database(dbase_path: Path, create_if_missing: bool) -> None:
    """Set the database at the given path to be used for database operations."""
    if not dbase_path.exists() and not create_if_missing:
        raise FileNotFoundError(
            f"The database at {dbase_path} was not found. Use `mircat-v2 dbase create {dbase_path}` to create one."
        )
    if create_if_missing and not dbase_path.exists():
        logger.info(f"Database not found, creating new database at {dbase_path}")
        conn = duckdb.connect(str(dbase_path))
        _create_tables_from_schema(conn)
        conn.close()
        logger.success(f"Database created at {dbase_path}")
    _save_dbase_path(dbase_path)
    logger.success(f"Set {dbase_path} as the database for mircat-v2.")


def update_database(dbase_path: Path | None = None) -> None:
    """Update an existing database schema to match the current mircat-v2 schema.

    This function will:
    1. Add new ENUM values to existing ENUMs
    2. Create new tables that don't exist
    3. Add new columns to existing tables

    Parameters
    ----------
    dbase_path : Path | None
        Path to the database file. If None, uses the configured database.
    """
    if dbase_path is None:
        config = read_dbase_config()
        dbase_path = Path(config["dbase_path"])

    if not dbase_path.exists():
        raise FileNotFoundError(
            f"Database file {dbase_path} not found. Use `mircat-v2 dbase create` to create one."
        )

    logger.info(f"Updating database schema at {dbase_path}")

    conn = duckdb.connect(str(dbase_path))
    try:
        # Parse the schema file
        with dbase_schema_file.open("r") as f:
            schema_script = f.read()

        # Update ENUMs
        _update_enums(conn, schema_script)

        # Update tables (create missing tables and add missing columns)
        _update_tables(conn, schema_script)

        logger.success(f"Database schema updated at {dbase_path}")
    finally:
        conn.close()


def _parse_enum_definitions(schema_script: str) -> dict[str, list[str]]:
    """Parse ENUM definitions from the schema script.

    Returns a dict mapping enum name to list of values.
    """
    enum_pattern = r"CREATE TYPE IF NOT EXISTS (\w+) AS ENUM \(([^)]+)\)"
    enums = {}
    for match in re.finditer(enum_pattern, schema_script):
        enum_name = match.group(1)
        values_str = match.group(2)
        values = [v.strip().strip("'") for v in values_str.split(",")]
        enums[enum_name] = values
    return enums


def _get_existing_enum_values(
    conn: duckdb.DuckDBPyConnection, enum_name: str
) -> list[str]:
    """Get existing values for an ENUM type from the database."""
    try:
        result = conn.execute(
            f"SELECT unnest(enum_range(NULL::{enum_name}))"
        ).fetchall()
        return [row[0] for row in result]
    except duckdb.CatalogException:
        return []


def _update_enums(conn: duckdb.DuckDBPyConnection, schema_script: str) -> None:
    """Update ENUM types to add any new values.

    DuckDB doesn't support ALTER TYPE ... ADD VALUE, so we need to drop and
    recreate ENUMs. This requires finding all columns using the ENUM,
    dropping them, recreating the ENUM, then recreating the columns.
    """
    schema_enums = _parse_enum_definitions(schema_script)

    for enum_name, schema_values in schema_enums.items():
        existing_values = _get_existing_enum_values(conn, enum_name)

        if not existing_values:
            # ENUM doesn't exist, create it
            values_str = ", ".join(f"'{v}'" for v in schema_values)
            conn.execute(f"CREATE TYPE {enum_name} AS ENUM ({values_str})")
            logger.info(f"Created ENUM type: {enum_name}")
            continue

        # Find new values that need to be added
        new_values = [v for v in schema_values if v not in existing_values]

        if new_values:
            # DuckDB doesn't support ALTER TYPE ADD VALUE, so we need to
            # drop and recreate the ENUM along with dependent columns
            _recreate_enum_with_new_values(conn, enum_name, schema_values)
            logger.info(f"Added values to ENUM {enum_name}: {', '.join(new_values)}")


def _get_columns_using_enum(
    conn: duckdb.DuckDBPyConnection, enum_name: str
) -> list[tuple[str, str]]:
    """Find all columns that use a specific ENUM type.

    Returns a list of (table_name, column_name) tuples.
    """
    # Query information_schema for columns with this enum type
    result = conn.execute(f"""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE data_type = '{enum_name}'
        AND table_schema = 'main'
    """).fetchall()
    return [(row[0], row[1]) for row in result]


def _recreate_enum_with_new_values(
    conn: duckdb.DuckDBPyConnection, enum_name: str, new_values: list[str]
) -> None:
    """Recreate an ENUM type with new values, preserving data in dependent columns.

    This is necessary because DuckDB doesn't support ALTER TYPE ... ADD VALUE.
    """
    # Find all columns using this enum
    dependent_columns = _get_columns_using_enum(conn, enum_name)

    # For each dependent column, convert to VARCHAR temporarily
    for table_name, col_name in dependent_columns:
        # Add a temporary VARCHAR column
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name}_temp VARCHAR")
        # Copy data to temp column (cast enum to varchar)
        conn.execute(f"UPDATE {table_name} SET {col_name}_temp = {col_name}::VARCHAR")
        # Drop the original enum column
        conn.execute(f"ALTER TABLE {table_name} DROP COLUMN {col_name}")

    # Drop the old enum type
    conn.execute(f"DROP TYPE {enum_name}")

    # Create the new enum with all values
    values_str = ", ".join(f"'{v}'" for v in new_values)
    conn.execute(f"CREATE TYPE {enum_name} AS ENUM ({values_str})")

    # Recreate the columns with the new enum type
    for table_name, col_name in dependent_columns:
        # Add the column back with the new enum type
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {enum_name}")
        # Copy data back from temp column
        conn.execute(
            f"UPDATE {table_name} SET {col_name} = {col_name}_temp::{enum_name}"
        )
        # Drop the temp column
        conn.execute(f"ALTER TABLE {table_name} DROP COLUMN {col_name}_temp")


def _parse_table_definitions(schema_script: str) -> dict[str, str]:
    """Parse CREATE TABLE statements from the schema script.

    Returns a dict mapping table name to full CREATE TABLE statement.
    """
    tables = {}
    # Split by CREATE TABLE to handle each table separately
    parts = re.split(r"(?=CREATE TABLE IF NOT EXISTS)", schema_script)
    for part in parts:
        match = re.match(
            r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.+)\)\s*;?\s*$", part, re.DOTALL
        )
        if match:
            table_name = match.group(1)
            table_def = match.group(2).strip()
            tables[table_name] = table_def
    return tables


def _parse_columns_from_definition(table_def: str) -> dict[str, str]:
    """Parse column definitions from a table definition string.

    Returns a dict mapping column name to column type/definition.
    """
    columns = {}
    # Split by comma, but be careful with CHECK constraints that contain commas
    parts = []
    depth = 0
    current = ""
    for char in table_def:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += char
    if current.strip():
        parts.append(current.strip())

    for part in parts:
        part = part.strip()
        # Skip PRIMARY KEY constraints
        if part.upper().startswith("PRIMARY KEY"):
            continue
        # Skip FOREIGN KEY constraints
        if part.upper().startswith("FOREIGN KEY"):
            continue
        # Parse column definition
        tokens = part.split(None, 1)
        if len(tokens) >= 2:
            col_name = tokens[0]
            col_type = tokens[1]
            columns[col_name] = col_type

    return columns


def _get_existing_tables(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Get list of existing tables in the database."""
    result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    return [row[0] for row in result]


def _get_existing_columns(
    conn: duckdb.DuckDBPyConnection, table: str
) -> dict[str, str]:
    """Get existing columns and their types for a table."""
    result = conn.execute(
        f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"
    ).fetchall()
    return {row[0]: row[1] for row in result}


def _update_tables(conn: duckdb.DuckDBPyConnection, schema_script: str) -> None:
    """Update tables to add missing tables and columns."""
    schema_tables = _parse_table_definitions(schema_script)
    existing_tables = _get_existing_tables(conn)

    for table_name, table_def in schema_tables.items():
        if table_name not in existing_tables:
            # Create the table
            conn.execute(f"CREATE TABLE {table_name} ({table_def})")
            logger.info(f"Created table: {table_name}")
            continue

        # Table exists, check for missing columns
        schema_columns = _parse_columns_from_definition(table_def)
        existing_columns = _get_existing_columns(conn, table_name)

        for col_name, col_type in schema_columns.items():
            if col_name not in existing_columns:
                # Remove CHECK constraints for ALTER TABLE (DuckDB may not support them in ALTER)
                col_type_clean = re.sub(r"\s*CHECK\s*\([^)]+\)", "", col_type).strip()
                conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_clean}"
                )
                logger.info(f"Added column '{col_name}' to table {table_name}")


def _save_dbase_path(dbase_path: Path) -> None:
    """Save the database path to the config file."""
    dbase_config = str(dbase_path.resolve())
    write_config(dbase_config, "dbase", "dbase_path")


def _create_tables_from_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Execute the DuckDB schema file to create all tables."""
    with dbase_schema_file.open("r") as f:
        schema_script = f.read()
    conn.execute(schema_script)


def _get_table_columns(conn: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    """Get the column names for a table from the database schema."""
    result = conn.execute(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"
    ).fetchall()
    return [row[0] for row in result]


def insert_data_batch(
    dbase_path: str | Path, table: str, data_records: list[dict], ignore: bool = False
) -> None:
    """Insert a batch of data into the database.

    Parameters
    ----------
    dbase_path : str | Path
        Path to the DuckDB database file.
    table : str
        Name of the table to insert into.
    data_records : list[dict]
        List of dictionaries containing the data to insert.
    ignore : bool
        If True, ignore primary key duplicates instead of replacing them.
        Default is False (replace duplicates).
    """
    if not data_records:
        return

    conn = duckdb.connect(str(dbase_path))
    try:
        # Check if table exists, create schema if not
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        ]
        if table not in tables:
            logger.info(f"Table {table} does not exist. Creating schema...")
            _create_tables_from_schema(conn)

        # Get column names from the database schema
        columns = _get_table_columns(conn, table)
        if not columns:
            raise ValueError(f"Table {table} not found in database schema.")

        # Filter records to only include valid columns
        insert_data = [
            {k: v for k, v in record.items() if k in columns} for record in data_records
        ]
        # Convert any numpy types to native Python types for DuckDB compatibility
        for record in insert_data:
            for k, v in record.items():
                if isinstance(v, np.generic):
                    record[k] = v.item()

        if insert_data:
            cols = list(insert_data[0].keys())
            placeholders = ", ".join(["?" for _ in cols])
            col_names = ", ".join(cols)

            # Use INSERT OR IGNORE to skip duplicates, or INSERT OR REPLACE to update them
            if ignore:
                sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"
            else:
                sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"

            # Prepare values
            values_list = [[record.get(col) for col in cols] for record in insert_data]

            conn.executemany(sql, values_list)
            logger.success(f"DBase: Inserted {len(values_list)} records into {table}")
    except Exception as e:
        logger.error(f"Error inserting batch into {table}: {e}")
        raise
    finally:
        conn.close()
