from __future__ import annotations

import os.path
from pathlib import Path
from typing import List, Sequence, Tuple, Union

from ewokscore import Task
from ImageD11 import grain as grainMod
from ImageD11.columnfile import columnfile as ColumnFile
from pydantic import Field
from ImageD11.grain import grain as Grain
from ..io import find_omega_slop
from ..models import InputsWithOverwrite, SampleConfig
from ..nexus.grains import save_nexus_grain_process
from ..nexus.peaks import save_column_file_as_ascii
from ..nexus.utils import (
    check_throw_write_data_group_url,
    get_data_url_paths,
    get_entry_name,
)
from ..grid_indexing.indexing import run_make_grain_map


class Inputs(InputsWithOverwrite):
    folder_file_config: SampleConfig
    indexed_grain_data_url: str = Field(
        description="Path to NXprocess group containing the indexed grains"
    )
    intensity_filtered_data_url: str = Field(
        description="Path to NXprocess group containing the filtered peaks used for the indexing"
    )
    hkl_tols: Sequence[float] = Field(
        description="Decreasing sequence of hkl tolerances. Will be used for iterative refinement (one after the other).",
        examples=[(0.3, 0.2, 0.1)],
    )
    minpks: int = Field(
        ge=0,
        description="Minimal number of peaks for the grain to be kept after iterative refinement.",
    )
    intensity_fine_filtered_data_url: Union[str, None] = Field(
        default=None,
        description="Path to NXprocess group containing the peaks to use to refine the grains finely at the end of the iterative refinement",
    )
    intensity_two_theta_range: Tuple[float, float] = Field(
        default=(0.0, 180.0), description="Range of two theta to use when refining"
    )
    symmetry: str = Field(
        default="cubic", description="Lattice symmetry used to further refine grains"
    )
    analyse_folder: Union[str, Path, None] = None
    lattice_file: str = Field(
        description="Path to the file (`.par` or `.cif`) containing lattice parameters and space group information forwarded by lattice filter task"
    )


class MakeGrainMap(Task, input_model=Inputs, output_names=["make_map_data_url"]):
    """
    Does an iterative refinement based on `hkl_tols` followed by a fine refinement on the indexed grains

    Outputs:
    - `ascii_grain_map_file`: file where the refined grains are saved
    """

    def run(self):
        inputs = Inputs(**self.get_input_values())
        nexus_file_path, intensity_filtered_data_path = get_data_url_paths(
            inputs.intensity_filtered_data_url
        )

        analyse_folder = (
            Path(inputs.analyse_folder)
            if inputs.analyse_folder
            else Path(nexus_file_path).parent
        )
        flt_pks_file = analyse_folder / "flt_3d_peaks.flt"
        save_column_file_as_ascii(
            inputs.intensity_filtered_data_url,
            flt_pks_file,
        )

        if inputs.intensity_fine_filtered_data_url is None:
            fine_flt_pks_file = flt_pks_file
        else:
            fine_flt_pks_file = analyse_folder / "fine_flt_3d_peaks.flt"
            save_column_file_as_ascii(
                inputs.intensity_fine_filtered_data_url,
                fine_flt_pks_file,
            )

        entry_name = get_entry_name(intensity_filtered_data_path)
        check_throw_write_data_group_url(
            overwrite=inputs.overwrite,
            filename=nexus_file_path,
            data_group_path=f"{entry_name}/make_map_grains",
        )

        geo_par_url = f"{nexus_file_path}::{entry_name}/geometry_updated_peaks"

        omega_slop = find_omega_slop(inputs.folder_file_config)
        grains_list, peaks_dict = self._run_make_grainMap(
            input_model=inputs,
            omega_slop=omega_slop,
            flt_pks_file=flt_pks_file,
            fine_flt_pks_file=fine_flt_pks_file,
            analyse_folder=analyse_folder,
            geo_par_url=geo_par_url,
        )
        makemap_grains_group_name = save_nexus_grain_process(
            filename=nexus_file_path,
            entry_name=entry_name,
            process_name="make_map_grains",
            config_settings={
                "intensity_tth_range": inputs.intensity_two_theta_range,
                "omega_slop": omega_slop,
                "hkl_tol": inputs.hkl_tols,
                "grains_came_from": inputs.indexed_grain_data_url,
                "peaks_came_from": inputs.intensity_filtered_data_url,
                "fine_peaks_came_from": inputs.intensity_fine_filtered_data_url,
                "minpks": inputs.minpks,
                "hkl_tol_seq": inputs.hkl_tols[-1],
                "symmetry": inputs.symmetry,
            },
            grains=grains_list,
            peaks_dict=peaks_dict,
            overwrite=inputs.overwrite,
        )
        self.outputs.make_map_data_url = makemap_grains_group_name

    def _run_make_grainMap(
        self,
        input_model: Inputs,
        omega_slop: float,
        flt_pks_file: Path,
        fine_flt_pks_file: Path,
        analyse_folder: Path,
        geo_par_url: str,
    ) -> List[Grain]:
        if not analyse_folder.exists():
            raise FileNotFoundError(
                f"Provided analyse Folder{analyse_folder} does not exist."
            )

        ubi_grain_file = os.path.join(analyse_folder, "refined_grains_map_file.flt")
        output_peaks_file = os.path.join(analyse_folder, "refined_peaks_map_file.flt")
        ubi_grain_file, output_peaks_file = run_make_grain_map(
            output_ubi_file=str(ubi_grain_file),
            indexed_grain_data_url=input_model.indexed_grain_data_url,
            geo_par_url=geo_par_url,
            lattice_file=input_model.lattice_file,
            hkl_tols=input_model.hkl_tols,
            omega_slop=omega_slop,
            intensity_two_theta_range=input_model.intensity_two_theta_range,
            symmetry=input_model.symmetry,
            flt_pks_file=flt_pks_file.absolute(),
            fine_flt_pks_file=fine_flt_pks_file.absolute(),
            minpks=input_model.minpks,
            output_peaks_file=output_peaks_file,
        )
        grains_list = grainMod.read_grain_file(filename=ubi_grain_file)
        peaks_cf = ColumnFile(filename=output_peaks_file)
        peaks_dict = {key: peaks_cf[key] for key in peaks_cf.keys()}
        return grains_list, peaks_dict
