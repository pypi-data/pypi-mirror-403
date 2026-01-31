from pathlib import Path
from typing import Optional

import h5py
from ewokscore import TaskWithProgress
from ImageD11 import frelon_peaksearch as gaussian_peak_search
from ..segmentation.lima import peaksearch as lima_peak_search
from ..io import extract_sample_info, get_monitor_scale_factor
from ..models import (
    InputsWithOverwrite,
    SegmenterConfig,
    GaussianPeakSearchConfig,
    LimaSegmenterAlgoConfig,
    SegmenterCorrectionFiles,
    SegmenterFolderConfig,
)
from ..nexus.peaks import save_nexus_process
from ..nexus.utils import group_exists
from ..tqdm_progress_callback import TqdmProgressCallback


class Inputs(InputsWithOverwrite):
    folder_config: SegmenterFolderConfig
    segmenter_algo_params: SegmenterConfig
    correction_files: SegmenterCorrectionFiles
    monitor_name: Optional[str] = None


class SegmentScan(
    TaskWithProgress,
    input_model=Inputs,
    output_names=["sample_folder_info", "segmented_peaks_url"],
):
    """
    This task segments an entire scan folder,
    merges the peaks, and produces a 3D column file.
    The resulting 3D column peak file is saved.

    Outputs:

    - `sample_folder_info`: A Config information about raw scan sample
    - `segmented_peaks_url`: A Nexus file data url path to `segmented_3d_peaks` data
    """

    def run(self):
        inputs = Inputs(**self.get_input_values())
        seg_folder_config = inputs.folder_config
        segmenter_cfg = inputs.segmenter_algo_params

        omega_motor = seg_folder_config.omega_motor
        master_file = seg_folder_config.master_file
        scan_number = seg_folder_config.scan_number
        analyse_folder = seg_folder_config.analyse_folder

        self.check_raw_master_file(master_file=master_file)
        output_folder = self.ensure_output_folder(
            master_file=master_file, analyse_folder=analyse_folder
        )
        nexus_file_path = self.check_nexus_file_overwrite(
            master_file=master_file,
            output_folder=output_folder,
            scan_number=scan_number,
            overwrite=inputs.overwrite,
        )

        if isinstance(segmenter_cfg, GaussianPeakSearchConfig):
            peak_3d_dict, segmenter_settings = self.run_gaussian_segmentation(
                inputs=inputs
            )
        elif isinstance(segmenter_cfg, LimaSegmenterAlgoConfig):
            peak_3d_dict, segmenter_settings = self.run_lima_segmentation(inputs=inputs)
        else:
            raise TypeError(f"Unsupported algorithm type: '{type(segmenter_cfg)}'")

        nxprocess_url = save_nexus_process(
            filename=nexus_file_path,
            entry_name=f"{scan_number}.1",
            process_name="segmented_3d_peaks",
            peaks_data=peak_3d_dict,
            config_settings={
                "FolderFileSettings": seg_folder_config.model_dump(),
                "Segmenter_settings": segmenter_settings,
            },
            overwrite=inputs.overwrite,
        )

        self.outputs.sample_folder_info = {
            "omega_motor": omega_motor,
            "master_file": master_file,
            "scan_number": scan_number,
        }
        self.outputs.segmented_peaks_url = nxprocess_url

    def run_gaussian_segmentation(self, inputs: Inputs) -> tuple[dict, dict]:
        segmenter_cfg = inputs.segmenter_algo_params
        correction_files_config = inputs.correction_files
        segmenter_settings = {
            "bgfile": correction_files_config.bg_file,
            "maskfile": correction_files_config.mask_file,
            "darkfile": correction_files_config.dark_file,
            "flatfile": correction_files_config.flat_file,
            "threshold": segmenter_cfg.threshold,
            "smoothsigma": segmenter_cfg.smooth_sigma,
            "bgc": segmenter_cfg.bgc,
            "minpx": segmenter_cfg.min_px,
            "m_offset_thresh": segmenter_cfg.offset_threshold,
            "m_ratio_thresh": segmenter_cfg.ratio_threshold,
        }
        seg_folder_config = inputs.folder_config
        scan_number = seg_folder_config.scan_number
        detector = seg_folder_config.detector
        omega_motor = seg_folder_config.omega_motor
        master_file = seg_folder_config.master_file
        master_file_path = Path(master_file)
        with h5py.File(master_file_path, "r") as hin:
            omega_array = hin[f"{scan_number}.1"]["measurement"][omega_motor][:].copy()

        monitor_name = inputs.monitor_name
        scale_factor = (
            None
            if monitor_name is None
            else get_monitor_scale_factor(master_file_path, scan_number, monitor_name)
        )

        all_frames_2d_peaks_list = gaussian_peak_search.segment_master_file(
            str(master_file_path),
            str(scan_number) + ".1" + "/measurement/" + detector,
            omega_array,
            segmenter_settings,
            scale_factor=scale_factor,
            tqdm_class=TqdmProgressCallback,
            TaskInstance=self,
        )
        peaks_2d_dict, num_peaks = gaussian_peak_search.peaks_list_to_dict(
            all_frames_2d_peaks_list
        )
        # 3d merge from 2d peaks dict
        peak_3d_dict = gaussian_peak_search.do3dmerge(
            peaks_2d_dict, num_peaks, omega_array
        )
        return peak_3d_dict, segmenter_settings

    def check_raw_master_file(self, master_file: str):
        master_file_path = Path(master_file)
        if not master_file_path.exists():
            raise FileNotFoundError(f"File `{master_file_path}` doesn't exist.")

    def ensure_output_folder(self, master_file: str, analyse_folder: str) -> Path:
        _, sample_name, dset_name = extract_sample_info(master_file=master_file)
        master_file_path = Path(master_file)
        if not master_file_path.exists():
            raise FileNotFoundError(f"File `{master_file_path}` doesn't exist.")

        output_folder = (
            Path(analyse_folder) / sample_name / f"{sample_name}_{dset_name}"
        )
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder

    def check_nexus_file_overwrite(
        self, master_file: str, output_folder: Path, scan_number: int, overwrite: bool
    ) -> str:
        _, sample_name, dset_name = extract_sample_info(master_file=master_file)
        nexus_file_path = output_folder / f"{sample_name}_{dset_name}.h5"
        seg_data_group_path = f"{scan_number}.1/segmented_3d_peaks"
        if not overwrite and group_exists(
            filename=nexus_file_path, data_group_path=seg_data_group_path
        ):
            raise ValueError(
                f"""Data group '{seg_data_group_path}' already exists in {nexus_file_path},
                Set `overwrite` to True if you wish to overwrite the existing data group.
                """
            )
        return nexus_file_path

    def run_lima_segmentation(self, inputs: Inputs) -> tuple[dict, dict]:
        segmenter_cfg = inputs.segmenter_algo_params
        correction_files_config = inputs.correction_files
        if correction_files_config.mask_file is None:
            raise ValueError("Mask file can't be None for Eiger detector")

        eiger_segmenter_settings = {
            "bg_file": correction_files_config.bg_file,
            "mask_file": correction_files_config.mask_file,
            "howmany": segmenter_cfg.max_pixels_per_frame,
            "pixels_in_spot": segmenter_cfg.num_pixels_in_spot,
            "cut": segmenter_cfg.lower_bound_cut,
        }
        seg_folder_config = inputs.folder_config
        scan_number = seg_folder_config.scan_number
        rot_motor = seg_folder_config.omega_motor
        detector = seg_folder_config.detector

        master_file = seg_folder_config.master_file
        self.ensure_output_folder(
            master_file=master_file, analyse_folder=seg_folder_config.analyse_folder
        )

        peaks_2d_dict = lima_peak_search(
            master_file=str(master_file),
            mask_file=str(correction_files_config.mask_file),
            analyse_folder=str(seg_folder_config.analyse_folder),
            segment_parameter=eiger_segmenter_settings,
            background_correction_file=correction_files_config.mask_file,
            scan_group=f"{scan_number}.1",
            detector_name=detector,
            omega_motor_name=rot_motor,
        )
        return peaks_2d_dict, eiger_segmenter_settings
