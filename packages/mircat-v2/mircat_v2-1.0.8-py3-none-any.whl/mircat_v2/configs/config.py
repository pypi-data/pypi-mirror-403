import json
import sys
from math import floor
from multiprocessing import cpu_count
from pathlib import Path
from loguru import logger

__all__ = [
    "config_path",
    "config_file",
    "read_config",
    "write_config",
    "read_segmentation_config",
    "read_dbase_config",
    "read_segmentation_config",
    "read_models_config",
    "read_stats_models_config",
    "logger_setup",
    "set_threads_per_process",
    "radiomics_config",
]


def generate_config() -> None:
    """Generate the default config"""
    with config_file.open("w") as f:
        json.dump(default_config, f, indent=2)


def read_config() -> dict[str, dict]:
    "Read and return the entire config file"
    try:
        with config_file.open() as f:
            return json.load(f)
    except json.decoder.JSONDecodeError as e:
        logger.error("the mircat-v2 config.json file could not be decoded.")
        raise e


def write_config(new_config: dict, key=str, subkey: str = None) -> None:
    """Write a new configuration to a specific key within the config.json file
    Parameters:
        new_config: dict - the new configuration to write
        key: str - the key that the configuration should be stored in, inside the config.json
    """
    config = read_config()
    if subkey is not None:
        config[key][subkey] = new_config
    else:
        config[key] = new_config
    with config_file.open("w") as f:
        json.dump(config, f, indent=2)
    logger.success(
        f"{key}{'[' + subkey + ']' if subkey is not None else ''} configuration saved to {config_file}"
    )


def read_segmentation_config() -> dict[str, dict]:
    "Read the config file and return the segmentation configuration"
    with config_file.open() as f:
        return json.load(f).get("segmentation", {})


def read_models_config() -> dict[str, dict]:
    "Read the config file and return the segmentation model configuration"
    with config_file.open() as f:
        return json.load(f).get("models", {})


def read_stats_models_config() -> dict[str, dict]:
    "Read the config file and return the stats models configuration"
    with config_file.open() as f:
        return json.load(f).get("stats_models", {})


def read_dbase_config() -> dict[str, dict]:
    """Read the config file and return the database configuration"""
    with config_file.open() as f:
        return json.load(f).get("dbase", {})


def logger_setup(verbose: bool, quiet: bool) -> None:
    """Set up logger for mircat-v2
    :param verbose: be verbose in the output by adding debug to stdout
    :param quiet: be quiet in the output by only showing successes and errors - no warnings or info.
    """
    logger.remove()
    # Regular
    stdout_fmt = "<green>{time: DD-MM-YYYY -> HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>"
    stderr_fmt = "<red>{time: DD-MM-YYYY -> HH:mm:ss}</red> | <level>{level}</level> | <level>{message}</level>"
    if quiet:
        # Only show success messages and error messages
        logger.add(
            sys.stdout,
            format=stdout_fmt,
            level="SUCCESS",
            filter=lambda record: record["level"].no <= 25,
            enqueue=True,
        )
        logger.add(sys.stderr, format=stderr_fmt, level="ERROR", enqueue=True)
    elif verbose:
        # Include debugging output
        logger.add(
            sys.stdout,
            format=stdout_fmt,
            level="DEBUG",
            filter=lambda record: record["level"].no <= 25,
            enqueue=True,
        )
        logger.add(
            sys.stderr,
            format=stderr_fmt,
            level="WARNING",
            enqueue=True,
        )
    else:
        # Show everything above INFO
        logger.add(
            sys.stdout,
            format=stdout_fmt,
            level="INFO",
            filter=lambda record: record["level"].no <= 25,
            enqueue=True,
        )
        logger.add(
            sys.stderr,
            format=stderr_fmt,
            level="WARNING",
            enqueue=True,
        )


def set_threads_per_process(args):
    # Do some thread matching
    total_threads = cpu_count()
    required_threads = args.n_processes * args.threads_per_process
    logger.debug(
        f"Total threads on machine: {total_threads}. Requested threads for segmentation: {required_threads}"
    )
    if total_threads < required_threads:
        # args.threads_per_process = floor(total_threads / args.n_processes)
        logger.warning(
            "Desired threads (n_processes * threads_per_process) > total threads on device ({}>{}). Monitor and change either the number of workers or threads if performance drops.",
            required_threads,
            total_threads,
            args.threads_per_process,
        )


config_path = Path(__file__).parent.resolve()
# Config will always be stored in the package files - easier to manage
config_file = config_path / "config.json"
radiomics_config = config_path / "radiomics_params.yaml"

needed_stats = {
    "999": {
        "background": 0,
        "spleen": 1,
        "kidney_right": 2,
        "kidney_left": 3,
        "gallbladder": 4,
        "liver": 5,
        "stomach": 6,
        "pancreas": 7,
        "adrenal_gland_right": 8,
        "adrenal_gland_left": 9,
        "lung_upper_lobe_left": 10,
        "lung_lower_lobe_left": 11,
        "lung_upper_lobe_right": 12,
        "lung_middle_lobe_right": 13,
        "lung_lower_lobe_right": 14,
        "esophagus": 15,
        "trachea": 16,
        "thyroid_gland": 17,
        "small_bowel": 18,
        "duodenum": 19,
        "colon": 20,
        "urinary_bladder": 21,
        "prostate": 22,
        "sacrum": 23,
        "vertebrae_S1": 24,
        "vertebrae_L5": 25,
        "vertebrae_L4": 26,
        "vertebrae_L3": 27,
        "vertebrae_L2": 28,
        "vertebrae_L1": 29,
        "vertebrae_T12": 30,
        "vertebrae_T11": 31,
        "vertebrae_T10": 32,
        "vertebrae_T9": 33,
        "vertebrae_T8": 34,
        "vertebrae_T7": 35,
        "vertebrae_T6": 36,
        "vertebrae_T5": 37,
        "vertebrae_T4": 38,
        "vertebrae_T3": 39,
        "vertebrae_T2": 40,
        "vertebrae_T1": 41,
        "vertebrae_C7": 42,
        "vertebrae_C6": 43,
        "vertebrae_C5": 44,
        "vertebrae_C4": 45,
        "vertebrae_C3": 46,
        "vertebrae_C2": 47,
        "vertebrae_C1": 48,
        "heart": 49,
        "aorta": 50,
        "pulmonary_vein": 51,
        "brachiocephalic_trunk": 52,
        "subclavian_artery_right": 53,
        "subclavian_artery_left": 54,
        "common_carotid_artery_right": 55,
        "common_carotid_artery_left": 56,
        "brachiocephalic_vein_left": 57,
        "brachiocephalic_vein_right": 58,
        "atrial_appendage_left": 59,
        "superior_vena_cava": 60,
        "inferior_vena_cava": 61,
        "portal_vein_and_splenic_vein": 62,
        "iliac_artery_left": 63,
        "iliac_artery_right": 64,
        "iliac_vena_left": 65,
        "iliac_vena_right": 66,
    },
    "485": {
        "background": 0,
        "subq_fat": 1,
        "visc_fat": 2,
        "skeletal_muscle": 3,
        "intermuscular_fat": 4,
    },
    "481": {"background": 0, "subq_fat": 1, "visc_fat": 2, "skeletal_muscle": 3},
    "299": {"background": 0, "body": 1, "body_extremities": 2},
    "300": {"background": 0, "body": 1, "body_extremities": 2},
}

# Default config - only stores dbase path (schema is in dbase_duckdb.sql)
default_config = {
    "dbase": {},
    "stats_models": needed_stats,
    "models": {},
}
if not config_file.exists():
    generate_config()
