from ewoks3dxrd.tasks.segment_scan import SegmentScan
from ..nexus.utils import get_data_url_paths, group_exists


def test_segmentation_lima(lima_inp_config):
    segmenter_config = {
        "algorithm": lima_inp_config.get("algorithm"),
        "lower_bound_cut": 1,
        "max_pixels_per_frame": 100000,
        "num_pixels_in_spot": 3,
        "intensity_pixel_avg_cutoff": 10,
    }
    file_cor_config = {
        "bg_file": lima_inp_config.get("bg_file"),
        "mask_file": lima_inp_config.get("mask_file"),
        "flat_file": None,
        "dark_file": None,
    }
    sample_folder_config = {
        "detector": lima_inp_config.get("detector"),
        "omega_motor": lima_inp_config.get("omega_motor"),
        "master_file": lima_inp_config["master_file"],
        "scan_number": lima_inp_config.get("scan_number"),
        "analyse_folder": lima_inp_config.get("analyse_folder"),
    }

    inputs = {
        "folder_config": sample_folder_config,
        "segmenter_algo_params": segmenter_config,
        "correction_files": file_cor_config,
    }

    task = SegmentScan(inputs=inputs)
    task.execute()
    nexus_file, nexus_group = get_data_url_paths(task.outputs["segmented_peaks_url"])
    assert group_exists(filename=nexus_file, data_group_path=nexus_group)
