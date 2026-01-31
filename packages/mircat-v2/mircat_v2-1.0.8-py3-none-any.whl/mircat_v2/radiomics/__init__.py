from pathlib import Path
from mircat_v2.radiomics.extractor import RadiomicsExtractor


def add_radiomics_subparser(subparsers):
    # Add subcommands
    radiomics_parser = subparsers.add_parser(
        "radiomics", help="Radiomics feature extraction commands"
    )
    radiomics_parser.add_argument(
        "niftis",
        type=Path,
        help="Path to the input image file or text file containing multiple paths",
    )
    radiomics_parser.add_argument(
        "--data-dir",
        "-d",
        type=Path,
        default=Path(""),
        help="Data directory for the input niftis (i.e. {data_dir}/nifti_path) - useful for remapping in docker. Default is no data directory.",
    )
    radiomics_parser.add_argument(
        "--labels",
        "-l",
        type=str,
        help="Label to extract features for, or a comma-separated list of labels. Default is all labels.",
        default="all",
    )
    radiomics_parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to a custom YAML configuration file for feature extraction parameters. Runs CT default otherwise.",
        default=None,
    )
    radiomics_parser.add_argument(
        "--database-insert",
        "-db",
        action="store_true",
        help="Flag to store the results of the radiomics extraction in your MirCAT-V2 database",
    )
    radiomics_parser.add_argument(
        "--overwrite",
        "-o",
        action="store_true",
        help="Re-extract and overwrite existing radiomics for specified structures. Default skips already-extracted structures.",
    )
    radiomics_parser.add_argument(
        "--ignore",
        action="store_true",
        help="Ignore primary key duplicates in database instead of replacing them. Default is to replace.",
    )
    radiomics_parser.add_argument(
        "--n-processes",
        "-n",
        type=int,
        default=1,
        help="Number of parallel processes for radiomics extraction. Default is 1 (sequential).",
    )
    radiomics_parser.add_argument(
        "--threads-per-process",
        "-t",
        type=int,
        default=4,
        help="Number of threads each process can use for SimpleITK/NumPy operations. Default is 4.",
    )
    return radiomics_parser


def run_radiomics(args):
    from mircat_v2.nifti import load_nifti_paths

    niftis = load_nifti_paths(args.niftis, args.data_dir)
    extractor = RadiomicsExtractor(
        args.labels,
        args.config,
        args.database_insert,
        args.overwrite,
        args.ignore,
        n_processes=args.n_processes,
        threads_per_process=args.threads_per_process,
        verbose=args.verbose,
        quiet=args.quiet,
    )
    extractor.extract_radiomics(niftis)
