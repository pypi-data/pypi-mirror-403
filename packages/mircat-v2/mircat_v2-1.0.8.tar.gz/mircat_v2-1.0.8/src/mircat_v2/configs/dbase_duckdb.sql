CREATE TYPE IF NOT EXISTS vertebrae AS ENUM ('S1', 'L5', 'L4', 'L3', 'L2', 'L1', 'T12', 'T11', 'T10', 'T9', 'T8', 'T7', 'T6', 'T5', 'T4', 'T3', 'T2', 'T1', 'C7', 'C6', 'C5', 'C4', 'C3', 'C2', 'C1');
CREATE TYPE IF NOT EXISTS aorta_regions AS ENUM ('whole', 'root', 'asc', 'arch', 'desc', 'up_abd', 'lw_abd');
CREATE TYPE IF NOT EXISTS tissue_volume_region AS ENUM ('total', 'abdominal', 'chest');
CREATE TYPE IF NOT EXISTS tissue_type AS ENUM ('subq_fat', 'visc_fat', 'skeletal_muscle', 'body', 'body_extremities');
CREATE TYPE IF NOT EXISTS tissue_measurement AS ENUM ('area_cm2', 'border_ratio', 'raw_perimeter_cm', 'ellipse_perimeter_cm', 'circle_perimeter_cm');
CREATE TYPE IF NOT EXISTS diameter_measurement AS ENUM ('mean', 'max', 'min', 'mid', 'proximal', 'distal');

CREATE TABLE IF NOT EXISTS conversions (
    series_uid VARCHAR CHECK (LENGTH(series_uid) <= 64), 
    study_uid VARCHAR CHECK (LENGTH(series_uid) <= 64), 
    nifti VARCHAR, 
    modality VARCHAR CHECK (LENGTH(modality) <= 5), 
    mrn VARCHAR, 
    accession VARCHAR, 
    series_name VARCHAR, 
    series_number INTEGER, 
    scan_date DATE, 
    original_series_name VARCHAR, 
    study_description VARCHAR, 
    ct_direction VARCHAR, 
    image_type VARCHAR, 
    sex VARCHAR, 
    age INTEGER, 
    birth_date DATE, 
    height_m DOUBLE, 
    weight_kg DOUBLE, 
    pregnancy_status INTEGER, 
    pixel_length_mm DOUBLE, 
    pixel_width_mm DOUBLE, 
    slice_thickness_mm DOUBLE, 
    manufacturer VARCHAR, 
    model VARCHAR, 
    kvp DOUBLE, 
    sequence_name VARCHAR, 
    protocol_name VARCHAR, 
    contrast_bolus_agent VARCHAR, 
    contrast_bolus_route VARCHAR, 
    contrast_bolus_volume DOUBLE, 
    dicom_folder VARCHAR, 
    conversion_date VARCHAR, 
    PRIMARY KEY (series_uid)
);

CREATE TABLE IF NOT EXISTS segmentations (
    nifti VARCHAR, 
    series_uid varchar(64), 
    task USMALLINT, 
    seg_file VARCHAR, 
    seg_date VARCHAR, 
    status VARCHAR, 
    failed_error VARCHAR, 
    PRIMARY KEY (nifti, task, seg_date)
);

CREATE TABLE IF NOT EXISTS metadata (
    nifti VARCHAR, 
    series_uid varchar(64), 
    study_uid varchar(64), 
    output_stats_file VARCHAR, 
    modality VARCHAR, 
    mrn VARCHAR CHECK (LENGTH(mrn) <= 10), 
    accession VARCHAR CHECK (LENGTH(accession) <= 12), 
    series_name VARCHAR, 
    series_number INTEGER, 
    scan_date DATE, 
    original_series_name VARCHAR, 
    study_description VARCHAR, 
    ct_direction VARCHAR, 
    abdominal_scan INTEGER, 
    chest_scan INTEGER, 
    correct_vertebrae_order INTEGER, 
    lowest_vertebra vertebrae, 
    highest_vertebra vertebrae, 
    image_type VARCHAR, 
    sex VARCHAR, 
    age INTEGER, 
    birth_date DATE, 
    height_m DOUBLE, 
    weight_kg DOUBLE, 
    pregnancy_status INTEGER, 
    pixel_length_mm DOUBLE, 
    pixel_width_mm DOUBLE, 
    slice_thickness_mm DOUBLE, 
    manufacturer VARCHAR, 
    model VARCHAR, 
    kvp DOUBLE, 
    sequence_name VARCHAR,
    protocol_name VARCHAR, 
    contrast_bolus_agent VARCHAR, 
    contrast_bolus_route VARCHAR, 
    contrast_bolus_volume DOUBLE, 
    dicom_folder VARCHAR, 
    conversion_date VARCHAR, 
    PRIMARY KEY (nifti)
);

CREATE TABLE IF NOT EXISTS vol_int (
                nifti VARCHAR, series_uid varchar(64), structure VARCHAR, volume_cm3 DOUBLE, hu_mean DOUBLE, hu_std_dev DOUBLE, PRIMARY KEY (nifti, structure)
            );
CREATE TABLE IF NOT EXISTS contrast (
                nifti VARCHAR, series_uid varchar(64), phase VARCHAR, probability DOUBLE, pi_time DOUBLE, pi_time_std DOUBLE, PRIMARY KEY (nifti)
            );
CREATE TABLE IF NOT EXISTS vertebrae (
                nifti VARCHAR, series_uid varchar(64), vertebra vertebrae, midline INTEGER, PRIMARY KEY (nifti, vertebra)
            );
CREATE TABLE IF NOT EXISTS aorta_metrics (
                nifti VARCHAR, series_uid varchar(64), region aorta_regions, entire_region TINYINT, length_mm DOUBLE, tortuosity_index DOUBLE, icm DOUBLE, n_inflections INTEGER, peria_volume_cm3 DOUBLE, peria_ring_volume_cm3 DOUBLE, peria_fat_volume_cm3 DOUBLE, peria_hu_mean DOUBLE, peria_hu_std DOUBLE, calc_volume_mm3 DOUBLE, calc_agatston DOUBLE, calc_count INTEGER, is_120_kvp INTEGER, mean_diameter_mm DOUBLE, mean_roundness DOUBLE, mean_flatness DOUBLE, PRIMARY KEY (nifti, region)
            );
CREATE TABLE IF NOT EXISTS aorta_diameters (
                nifti VARCHAR, series_uid varchar(64), region aorta_regions, measure diameter_measurement, mean_diameter_mm DOUBLE, major_diameter_mm DOUBLE, minor_diameter_mm DOUBLE, area_mm2 DOUBLE, roundness DOUBLE, flatness DOUBLE, rel_distance DOUBLE, entire_region INTEGER, PRIMARY KEY (nifti, region, measure)
            );
CREATE TABLE IF NOT EXISTS tissues_volumetric (
                nifti VARCHAR, series_uid varchar(64), region tissue_volume_region, structure tissue_type, volume_cm3 DOUBLE, hu_mean DOUBLE, hu_std_dev DOUBLE, PRIMARY KEY (nifti, region, structure)
            );
CREATE TABLE IF NOT EXISTS tissues_vertebral (
                nifti VARCHAR, series_uid varchar(64), vertebra vertebrae, structure tissue_type, measurement tissue_measurement, value DOUBLE, PRIMARY KEY (nifti, vertebra, structure, measurement)
            );
CREATE TABLE IF NOT EXISTS iliac (
                nifti VARCHAR, series_uid varchar(64), side VARCHAR, length_mm DOUBLE, location diameter_measurement, metric VARCHAR, value DOUBLE, PRIMARY KEY (nifti, side, location, metric)
            );
CREATE TABLE IF NOT EXISTS radiomics (
                nifti VARCHAR, series_uid varchar(64), mrn VARCHAR, accession VARCHAR, series_name VARCHAR, series_number INTEGER, scan_date DATE, structure VARCHAR, transformation VARCHAR, feature_class VARCHAR, feature_name VARCHAR, feature_value DOUBLE, PRIMARY KEY (nifti, structure, transformation, feature_class, feature_name)
            );