from __future__ import annotations
import os.path
import logging
from pathlib import Path
from typing import List
from ImageD11.grain import grain as Grain
from ImageD11.columnfile import columnfile as ColumnFile

from .make_grain_map import MakeGrainMap, Inputs
from ImageD11 import grain as grainMod
from ..grid_indexing.indexing import run_make_map_grain_in_subprocess
from ..sub_process_task_mixin import SubprocessTaskMixin

_logger = logging.getLogger(__name__)


class MakeGrainMapSubProcess(SubprocessTaskMixin, MakeGrainMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_sub_process_attributes()
        self._grain_file: str | None = None

    def _run_make_grainMap(
        self,
        input_model: Inputs,
        omega_slop: float,
        flt_pks_file: Path,
        fine_flt_pks_file: Path,
        analyse_folder: Path,
        geo_par_url: str,
    ) -> List[Grain]:
        """
        Docstring for _run_make_grainMap

        :param input_model: Same as MakeGrainMap input model
        :type input_model: Inputs

        :param omega_slop: This is a slop of the rotation motor diffrz for ID11 or Omega for ID03
        :type omega_slop: float

        :param flt_pks_file: strongly filtered peaks column File
        :type flt_pks_file: Path
        :param fine_flt_pks_file: Lattice and/or Intensity filtered peaks column File
        :type fine_flt_pks_file: Path

        :param analyse_folder: Path to store the results
        :type analyse_folder: Path

        :param geo_par_url: lap geometry parameters as data url
        :type geo_par_url: str

        :return: returns the generated grain class of ImageD11 that contains UBI, translation and other attributes
        :rtype: List[grain]
        """
        output_peaks_file = os.path.join(analyse_folder, "refined_peaks_map_file.flt")
        self._grain_file = os.path.join(analyse_folder, "refined_grains_map_file.map")

        proc, ubi_file, peaks_file = self._start_subprocess(
            run_make_map_grain_in_subprocess,
            analyse_folder=analyse_folder,
            output_ubi_file=str(self._grain_file),
            indexed_grain_data_url=input_model.indexed_grain_data_url,
            geo_par_url=geo_par_url,
            lattice_file=input_model.lattice_file,
            hkl_tols=input_model.hkl_tols,
            omega_slop=omega_slop,
            intensity_two_theta_range=input_model.intensity_two_theta_range,
            symmetry=input_model.symmetry,
            flt_pks_file=str(flt_pks_file),
            fine_flt_pks_file=str(fine_flt_pks_file),
            minpks=input_model.minpks,
            output_peaks_file=output_peaks_file,
        )
        self._init_event.set()
        proc.wait()
        self.stop()

        grains_list = grainMod.read_grain_file(filename=ubi_file)
        peaks_cf = ColumnFile(filename=output_peaks_file)
        peaks_dict = {key: peaks_cf[key] for key in peaks_cf.keys()}
        return grains_list, peaks_dict

    def get_grain_file(self) -> str:
        return self._grain_file
