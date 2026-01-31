from pathlib import Path

import numpy as np
import polars as pl
import SimpleITK as sitk
from loguru import logger
from radiomics import featureextractor, setVerbosity

from mircat_v2.configs import (
    radiomics_config,
    read_dbase_config,
    read_stats_models_config,
)
from mircat_v2.dbase import insert_data_batch
from mircat_v2.nifti import Nifti
from mircat_v2.parallel import batched, run_parallel
from mircat_v2.stats.utilities import calculate_shape_stats

stats_configs = read_stats_models_config()
allowed_structures = set(["abd_aorta"])
structure_to_model_map = {"abd_aorta": "999"}
structure_to_label_map = {"abd_aorta": 50}
for model_id, model in stats_configs.items():
    for structure, label in model.items():
        if structure != "background":
            allowed_structures.add(structure)
            structure_to_model_map[structure] = model_id
            structure_to_label_map[structure] = label


class RadiomicsExtractor:
    # This does not change across instances
    structure_to_model_map = structure_to_model_map
    structure_to_label_map = structure_to_label_map

    # Initialize with custom labels and config path
    def __init__(
        self,
        structures,
        config_path=None,
        save_to_database=False,
        overwrite=False,
        ignore=False,
        n_processes=1,
        threads_per_process=4,
        verbose=False,
        quiet=False,
    ):
        if config_path is None:
            self.config_path = radiomics_config
        else:
            self.config_path = config_path

        if isinstance(structures, list):
            pass
        elif Path(structures).exists():
            with open(structures) as f:
                structures = f.read().splitlines()
        elif "," in structures:
            structures = structures.split(",")
        elif structures == "all":
            structures = list(allowed_structures)
        else:
            structures = [structures]
        self.structures = self._validate_structures(structures)
        self.save_to_database = save_to_database
        if save_to_database:
            self.dbase_config = read_dbase_config()
        else:
            self.dbase_config = {}
        self.overwrite = overwrite
        self.ignore = ignore
        self.n_processes = n_processes
        self.threads_per_process = threads_per_process
        self.verbose = verbose
        self.quiet = quiet

    @staticmethod
    def _validate_structures(structures) -> list[str]:
        """Validate that given structures are in the allowed structures set.
        Parameters
        ----------
        structures : list[str] - the list of structures to validate against the allowed structures set.

        Returns
        -------
        list[str] - the validated list of structures that are allowed.
        """
        invalid = set(structures).difference(allowed_structures)
        if invalid:
            logger.warning(
                f"Invalid labels detected: {invalid}. Allowed labels are: {allowed_structures}"
            )
            structures = list(set(structures).difference(invalid))
        logger.info(
            f"Extracting radiomics for {len(structures)} structure{'s' if len(structures) != 1 else ''} from CT."
        )
        logger.debug(f"Structures: {structures}")
        return structures

    def _get_existing_structures(self, nifti_obj: Nifti) -> set[str]:
        """Return set of structures already extracted for this nifti."""
        output_file = nifti_obj.seg_folder / f"{nifti_obj.name}_radiomics.parquet"
        if not output_file.exists():
            return set()
        structures = (
            pl.scan_parquet(output_file)
            .select("structure")
            .unique()
            .collect()
            .get_column("structure")
            .to_list()
        )
        return set(structures)

    def _on_radiomics_complete(self, current: int, total: int, result) -> None:
        """Callback for live progress logging."""
        if result is None:
            logger.error(f"Radiomics [{current}/{total}] ({current / total:.2%}) ✗")
        else:
            nifti_name, _, _ = result
            logger.success(
                f"Radiomics [{current}/{total}] ({current / total:.2%}) ✓ {nifti_name}"
            )

    def _insert_batch_to_db(self, results: list[tuple]) -> None:
        """Insert a batch of radiomics results into the database."""
        all_records = []
        for result in results:
            if result is None:
                continue
            _, radiomics_df, _ = result
            if radiomics_df is not None:
                records = radiomics_df.with_columns(
                    pl.col("scan_date").cast(pl.String)
                ).to_dicts()
                all_records.extend(records)
        if all_records:
            insert_data_batch(
                self.dbase_config["dbase_path"], "radiomics", all_records, self.ignore
            )

    def extract_radiomics(self, niftis: list[Path], batch_size: int = 20):
        """Extract the radiomic features from a list of NIfTI files.
        Parameters
        ----------
        niftis : list[Path]
            List of paths to NIfTI files from which to extract radiomic features.
        batch_size : int
            Number of nifti files to process before inserting to database.
        """
        self.total_niftis = len(niftis)
        if self.n_processes > 1:
            logger.info(
                f"Starting radiomics extraction on {self.total_niftis} nifti files with {self.n_processes} processes."
            )
        else:
            logger.info(
                f"Starting radiomics extraction on {self.total_niftis} nifti files."
            )

        for batch in batched(niftis, batch_size):
            results, was_interrupted = run_parallel(
                self._process_single_nifti,
                batch,
                n_jobs=self.n_processes,
                threads_per_job=self.threads_per_process,
                verbose=self.verbose,
                quiet=self.quiet,
                on_complete=self._on_radiomics_complete,
            )

            if self.save_to_database:
                self._insert_batch_to_db(results)

            if was_interrupted:
                raise SystemExit(130)

    def _process_single_nifti(self, nifti_path: Path) -> tuple | None:
        """Process a single NIfTI file for radiomics extraction. Worker method for parallel processing.

        Parameters
        ----------
        nifti_path : Path
            Path to the NIfTI file to process.

        Returns
        -------
        tuple | None
            (nifti_name, radiomics_df, structures_extracted) on success, None on failure.
        """
        try:
            nifti_obj = Nifti(nifti_path)
            structures_to_extract = self.structures.copy()

            if not self.overwrite:
                existing = self._get_existing_structures(nifti_obj)
                structures_to_extract = [
                    s for s in structures_to_extract if s not in existing
                ]
                skipped = existing.intersection(set(self.structures))
                if skipped:
                    logger.debug(
                        f"Skipping already-extracted structures for {nifti_obj.name}: {skipped}"
                    )

            if not structures_to_extract:
                return (nifti_obj.name, None, [])

            extracted = self._extract_radiomics(nifti_obj, structures_to_extract)
            radiomics_df = self.save_radiomics_to_file(nifti_obj, extracted)
            return (nifti_obj.name, radiomics_df, structures_to_extract)
        except Exception as e:
            logger.error(f"Error processing {nifti_path}: {e}")
            return None

    def _extract_radiomics(self, nifti_obj: Nifti, structures: list[str]) -> None:
        """Radiomics extraction from a nifti file. Saves the extracted features to a file in the segmentation folder.
        Parameters
        ----------
        nifti : Path
            Path to the NIfTI file from which to extract radiomic features.
        structures : list[str]
            List of structures to extract radiomic features for.
        returns:
            None
        """
        segmentations = nifti_obj.segmentations
        # This is the map for older versions of the same model to mapped to the same config
        old_to_new_map = {"total": "999", "tissues": "481", "body": "299", "998": "999"}
        # Get the id map
        id_to_segmentation_map = {}
        for seg in segmentations:
            seg_id = seg.parts[-1].split("_")[-1].split(".")[0]
            seg_id = old_to_new_map.get(seg_id, seg_id)
            id_to_segmentation_map[seg_id] = sitk.ReadImage(seg)
        # Abdominal Aorta is a special
        if "abd_aorta" in structures:
            structures = [
                structure for structure in structures if structure != "abd_aorta"
            ]
            abd_aorta = True
        else:
            abd_aorta = False
        # Read in the image
        setVerbosity(40)
        extractor = featureextractor.RadiomicsFeatureExtractor(str(self.config_path))
        image = nifti_obj.img
        radiomics_output = {}
        for structure in structures:
            seg_id = structure_to_model_map.get(structure)
            if seg_id in id_to_segmentation_map:
                segmentation = id_to_segmentation_map[seg_id]
                label = structure_to_label_map[structure]
                radiomics_output[structure] = {
                    k: v.item()
                    for k, v in extractor.execute(
                        image, segmentation, label=label
                    ).items()
                    if "diagnostics" not in k
                }
        if not abd_aorta:
            return radiomics_output
        # TODO Add abdominal aorta extraction
        seg_id = structure_to_model_map.get("abd_aorta")
        if seg_id in id_to_segmentation_map:
            segmentation = id_to_segmentation_map[seg_id]
            shape_stats = calculate_shape_stats(segmentation)
            if structure_to_label_map.get("abd_aorta") not in shape_stats.GetLabels():
                logger.debug("No abdominal aorta found in this segmentation")
                return radiomics_output
            vertebrae_labels = {
                k.replace("vertebrae_", ""): v
                for k, v in structure_to_label_map.items()
                if "vertebrae" in k.lower()
            }
            vertebrae_stats = {}
            previous_midline = 0
            correct_vertebrae_order = 1
            for vertebra, label in vertebrae_labels.items():
                if label in shape_stats.GetLabels():
                    vertebra_indicies = shape_stats.GetIndexes(label)
                    z_indices = vertebra_indicies[2::3]
                    midline = int(np.median(z_indices))
                    vertebrae_stats[vertebra] = midline
                    if midline <= previous_midline:
                        correct_vertebrae_order = 0
                else:
                    vertebrae_stats[vertebra] = None
            logger.debug(f"Vertebrae indices: {vertebrae_stats}")
            # L5 is lower in the index than T12
            if correct_vertebrae_order == 0:
                logger.debug(
                    "Vertebrae order is incorrect. Abdominal aorta extraction may be inaccurate."
                )
            abd_verts = [
                v
                for k, v in vertebrae_stats.items()
                if v is not None and k in ["L5", "L4", "L3", "L2", "L1", "T12"]
            ]
            lowest = abd_verts[0] if abd_verts else None
            highest = abd_verts[-1] if abd_verts else None
            l5 = vertebrae_stats.get("L5")
            t12 = vertebrae_stats.get("T12")
            # Track if the abdominal aorta is partial or whole
            whole = 1.0
            if len(abd_verts) < 3:
                logger.warning(
                    f"Not enough vertebrae found to extract abdominal aorta: {nifti_obj.path}"
                )
                return radiomics_output
            elif l5 is None and t12 is None:
                logger.warning(f"Abdominal aorta is not available: {nifti_obj.path}")
                return radiomics_output
            if l5 is None:
                logger.warning(f"Could not find L5 vertebra in {nifti_obj.path}. ")
                whole = 0
            elif t12 is None:
                logger.warning(f"Could not find T12 vertebra in {nifti_obj.path}. ")
                whole = 0
            image = image[..., lowest:highest]
            segmentation = segmentation[..., lowest:highest]
            label = structure_to_label_map["abd_aorta"]
            radiomics_output["abd_aorta"] = {
                k: v.item()
                for k, v in extractor.execute(image, segmentation, label=label).items()
                if "diagnostics" not in k
            }
            radiomics_output["abd_aorta"].update({"original_shape_is-whole": whole})
        return radiomics_output

    def save_radiomics_to_file(
        self, nifti_obj: Nifti, extracted_radiomics: dict
    ) -> dict:
        """Save extracted radiomics to a file in the segmentations directory of the nifti. Will check for previous radiomics before writing.
        Radiomics file will be saved to {nifti.seg_folder} /  {nifti.name}_radiomics.parquet

        Parameters
        ----------
        nifti_obj:
            the Nifti object containing metadata information
        extracted_radiomics:
            the output of _extract_radiomics

        Returns
        -------
        The dataframe that is saved to a parquet file.
        """
        output_file = Path(f"{nifti_obj.seg_folder}/{nifti_obj.name}_radiomics.parquet")
        if output_file.exists():
            radiomics_df = pl.read_parquet(output_file)
            # If overwriting, remove existing rows for structures being re-extracted
            if self.overwrite:
                structures_to_replace = set(extracted_radiomics.keys())
                radiomics_df = radiomics_df.filter(
                    ~pl.col("structure").is_in(structures_to_replace)
                )
        else:
            radiomics_df = pl.DataFrame(
                schema={
                    "nifti": pl.String,
                    "series_uid": pl.String,
                    "mrn": pl.String,
                    "accession": pl.String,
                    "series_name": pl.String,
                    "series_number": pl.Int64,
                    "scan_date": pl.Date,
                    "structure": pl.String,
                    "transformation": pl.String,
                    "feature_class": pl.String,
                    "feature_name": pl.String,
                    "feature_value": pl.Float64,
                }
            )
        nifti_metadata = nifti_obj.metadata
        nifti_path = str(nifti_obj.path)
        series_uid = nifti_metadata.get("series_uid")
        mrn = nifti_metadata.get("mrn")
        accession = nifti_metadata.get("accession")
        series_name = nifti_metadata.get("series_name")
        series_number = nifti_metadata.get("series_number")
        scan_date = nifti_metadata.get("scan_date", "1900-1-1")
        # Aggregate all radiomics data into a dataframe
        extracted_rows = [
            [
                nifti_path,
                series_uid,
                mrn,
                accession,
                series_name,
                series_number,
                scan_date,
                structure,
                sub_key,
                value,
            ]
            for structure, sub_dict in extracted_radiomics.items()
            for sub_key, value in sub_dict.items()
        ]
        extracted_df = (
            pl.DataFrame(
                extracted_rows,
                schema={
                    "nifti": pl.String,
                    "series_uid": pl.String,
                    "mrn": pl.String,
                    "accession": pl.String,
                    "series_name": pl.String,
                    "series_number": pl.Int64,
                    "scan_date": pl.String,
                    "structure": pl.String,
                    "feature_id": pl.String,
                    "feature_value": pl.Float64,
                },
                orient="row",
            )
            .with_columns(
                pl.col("feature_id")
                .str.split_exact("_", 3)
                .struct.rename_fields(
                    ["transformation", "feature_class", "feature_name"]
                ),
                pl.col("scan_date").cast(pl.Date),
            )
            .unnest("feature_id")
            .select(radiomics_df.columns)
        )
        radiomics_df = (
            radiomics_df.vstack(extracted_df)
            .unique()
            .sort("structure", "transformation", "feature_class")
        )
        radiomics_df.write_parquet(output_file)
        return radiomics_df

