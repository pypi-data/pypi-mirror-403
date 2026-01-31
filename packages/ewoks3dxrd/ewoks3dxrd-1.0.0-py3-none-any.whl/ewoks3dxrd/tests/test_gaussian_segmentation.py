from ewoks3dxrd.tasks.segment_scan import SegmentScan
from ..nexus.utils import get_data_url_paths, group_exists


def test_gaussian_segmentation(inp_config):
    segmenter_config = {
        "algorithm": "gaussian_peak_search",
        "threshold": 70,
        "smooth_sigma": 1.0,
        "bgc": 0.9,
        "min_px": 3,
        "offset_threshold": 100,
        "ratio_threshold": 150,
    }
    file_cor_config = {
        "bg_file": inp_config.get("bg_file"),
        "mask_file": inp_config.get("mask_file"),
        "flat_file": None,
        "dark_file": None,
    }
    sample_folder_config = {
        "detector": inp_config.get("detector"),
        "omega_motor": inp_config.get("omega_motor"),
        "master_file": inp_config.get("master_file"),
        "scan_number": inp_config.get("scan_number"),
        "analyse_folder": inp_config.get("analyse_folder"),
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
