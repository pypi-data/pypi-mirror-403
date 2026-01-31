from pathlib import Path

from loguru import logger

from mircat_v2.configs import read_dbase_config, read_stats_models_config
from mircat_v2.dbase import insert_data_batch
from mircat_v2.nifti import NotNiftiFileError, SimpleITKReadError, StatsNifti
from mircat_v2.parallel import batched, run_parallel
from mircat_v2.stats.aorta import calculate_aorta_stats
from mircat_v2.stats.contrast import predict_contrast
from mircat_v2.stats.iliac import calculate_iliac_artery_stats
from mircat_v2.stats.tissues import calculate_tissue_stats
from mircat_v2.stats.vertebrae import calculate_vertebrae_stats
from mircat_v2.stats.vol_int import calculate_volume_and_intensity_stats


STATS_DB_TABLES = [
    "metadata",
    "vol_int",
    "contrast",
    "vertebrae",
    "aorta_metrics",
    "aorta_diameters",
    "tissues_volumetric",
    "tissues_vertebral",
    "iliac",
]


class Analyzer:
    """Analyzer class for processing and analyzing tasks with specified parameters."""

    # Map for resolution settings
    resolution_map = {
        "normal": [1.0, 1.0, 1.0],
        "high": [0.75, 0.75, 0.75],
        "highest": [0.5, 0.5, 0.5],
    }
    # Segmentations needed for specific tasks in order of preference
    task_map = {
        "vol_int": ["998", "999", "total"],
        "contrast": ["998", "999", "total"],
        "vertebrae": ["998", "999", "total"],
        "aorta": ["998", "999", "total"],
        "tissues": ["485", "481", "tissues"],
        "body": ["299", "300", "body"],
        "iliac": ["998", "999", "total"],
    }

    def __init__(
        self,
        niftis: list[Path],
        task_list: list[str],
        resolution: str,
        image_resampler: str,
        label_resampler: str,
        n_processes: int,
        threads_per_process: int,
        dbase_insert: bool = False,
        overwrite: bool = False,
        gzip: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        ignore: bool = False,
    ):
        self.niftis = niftis
        self.total_niftis = len(niftis)
        if task_list == ["all"]:
            task_list = list(self.task_map.keys())
        # This orders the tasks by the order they are defined in task_map
        self.task_list = [task for task in self.task_map if task in task_list]
        if "tissues" in self.task_list and "body" not in task_list:
            self.task_list.append("body")
        self.resolution = self.resolution_map.get(resolution)
        self.image_resampler = image_resampler
        self.label_resampler = label_resampler
        self.n_processes = n_processes
        self.threads_per_process = threads_per_process
        # Read database configuration if dbase_insert is True
        self.dbase_insert = dbase_insert
        if dbase_insert:
            self.dbase_config = read_dbase_config()
        else:
            self.dbase_config = {}
        # Read segmentation configuration
        # We only need the labels for each task
        self.segmentation_labels = read_stats_models_config()
        self.overwrite = overwrite
        self.gzip = gzip
        self.verbose = verbose
        self.quiet = quiet
        self.ignore = ignore

    def analyze(self, nifti_path: Path | str) -> dict|None:
        """Analyze a single nifti file. Worker method for parallel processing.
        :param nifti_path: Path to the nifti file to analyze.
        """
        try:
            nifti = StatsNifti(nifti_path, self.overwrite)
            # Preprocess the nifti file for statistics
            (
                nifti.check_for_segmentations(
                    self.task_list, self.task_map
                ).preprocess_for_stats(
                    self.resolution, self.image_resampler, self.label_resampler
                )
            )
            self.analyze_tasks(nifti)
            nifti.save_json_stats(self.gzip)
            if self.dbase_insert:
                nifti.format_stats_for_db()
                return nifti.db_stats
            else:
                return {}
        except SimpleITKReadError:
            logger.error(f"Could not read nifti file: {nifti_path}. Skipping.")
            return None
        except FileNotFoundError:
            return None
        except NotNiftiFileError:
            return None

    def analyze_tasks(self, nifti: StatsNifti) -> None:
        for task in self.task_list:
            if task not in nifti.task_to_id_map:
                logger.warning(
                    f"Segmentation for task '{task}' not found in {nifti.path}. Skipping."
                )
                continue
            seg_id = nifti.task_to_id_map[task]
            seg_labels = self.segmentation_labels[seg_id]
            try:
                match task:
                    case "vol_int":
                        vol_int_stats = calculate_volume_and_intensity_stats(
                            nifti, seg_id, seg_labels
                        )
                        nifti.add_stats("vol_int", vol_int_stats)
                    case "contrast":
                        if not nifti.stats.get("vol_int", {}):
                            logger.warning(
                                "Organ intensities are needed for contrast prediction. Skipping contrast task."
                            )
                            continue
                        contrast_stats = predict_contrast(nifti.stats["vol_int"])
                        nifti.add_stats("contrast", contrast_stats)
                    case "vertebrae":
                        vertebrae_stats = calculate_vertebrae_stats(
                            nifti, seg_id, seg_labels
                        )
                        # Add the structural vert stats to the metadata for easy searching
                        for key in [
                            "lowest_vertebra",
                            "highest_vertebra",
                            "correct_vertebrae_order",
                            "abdominal_scan",
                            "chest_scan",
                        ]:
                            nifti.add_stats(
                                key, vertebrae_stats.pop(key, None), "metadata"
                            )
                        nifti.add_stats("vertebrae", vertebrae_stats)
                        nifti.set_vertebrae_midlines(vertebrae_stats)
                    case "aorta":
                        aorta_stats = calculate_aorta_stats(nifti, seg_id, seg_labels)
                        nifti.add_stats("aorta", aorta_stats)
                    case "tissues":
                        # Need body segmentation for tissue stats
                        body_seg_id = nifti.task_to_id_map.get("body", None)
                        if not body_seg_id:
                            logger.warning(
                                "Body segmentation is required for tissue statistics. Skipping tissue task."
                            )
                            continue
                        body_labels = self.segmentation_labels[body_seg_id]
                        tissue_stats = calculate_tissue_stats(
                            nifti, seg_id, seg_labels, body_seg_id, body_labels
                        )
                        nifti.add_stats("tissues", tissue_stats)
                    case "iliac":
                        iliac_stats = calculate_iliac_artery_stats(
                            nifti, seg_id, seg_labels
                        )
                        nifti.add_stats("iliac", iliac_stats)
            except Exception as e:
                logger.error(f"Error calculating {task} statistics: {e}")

    def _on_stats_complete(self, current: int, total: int, result) -> None:
        """Callback for live progress logging."""
        if result is None:
            logger.error(f"Stats [{current}/{total}] ({current / total:.2%}) ✗")
        else:
            logger.opt(ansi=True).info(
                f"Stats [{current}/{total}] ({current / total:.2%}) <green>✓</green>"
            )

    def _insert_batch_to_db(self, results: list[dict|None]) -> None:
        """Insert a batch of results into the database."""
        # Aggregate all db_stats from results
        batch_data = {table: [] for table in STATS_DB_TABLES}
        for result in results:
            if result:
                for key, list_data in result.items():
                    batch_data[key].extend(list_data)
        # Insert each table's data
        for table, list_data in batch_data.items():
            if list_data:
                insert_data_batch(
                    self.dbase_config["dbase_path"], table, list_data, self.ignore
                )

    def run(self, batch_size: int = 50) -> None:
        """Run the analysis on the provided NiFTi files.
        :param batch_size: Number of nifti files to process before inserting to database.
        """
        if self.n_processes > 1:
            logger.info(f"Running analysis with {self.n_processes} processes.")
        else:
            logger.info("Running analysis with single process.")
        logger.info(
            f"Using resolution: {self.resolution} mm, image resampler: {self.image_resampler}, label resampler: {self.label_resampler}."
        )
        logger.info(f"Tasks to run: {self.task_list}.")
        

        total_batches = (self.total_niftis + batch_size - 1) // batch_size
        logger.info(f"Starting analysis on {self.total_niftis} nifti files - {total_batches} batches of {batch_size} files each.")
        for i, batch in enumerate(batched(self.niftis, batch_size), start=1):
            results, was_interrupted = run_parallel(
                self.analyze,
                batch,
                n_jobs=self.n_processes,
                threads_per_job=self.threads_per_process,
                verbose=self.verbose,
                quiet=self.quiet,
                on_complete=self._on_stats_complete,
            )
            logger.success(f"Batch [{i}/{total_batches}] complete.")
            if self.dbase_insert:
                self._insert_batch_to_db(results)

            if was_interrupted:
                raise SystemExit(130)
