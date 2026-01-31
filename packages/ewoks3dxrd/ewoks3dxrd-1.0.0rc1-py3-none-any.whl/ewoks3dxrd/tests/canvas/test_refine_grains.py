import shutil
from orangecontrib.ewoks3dxrd.make_map_grains import OWMakeGrainMap


def test_make_map_dynamic_input(qtapp, tmp_path):  # noqa F401
    widget = OWMakeGrainMap()
    dest_file = tmp_path / "nexus_segment.h5"
    shutil.copy2(
        "/data/projects/id03_3dxrd/ewoks_test_data/nexus_segment.h5",
        dest_file,
    )
    master_file = "/data/projects/id03_3dxrd/expt/RAW_DATA/FeAu_0p5_tR/FeAu_0p5_tR_ff1/FeAu_0p5_tR_ff1.h5"
    widget._sampleFolderConfig._masterFilePath.setText(file_path=master_file)
    widget._sampleFolderConfig._fillDefaultValues(master_file_path=master_file)

    grainURL = f"{dest_file}::/1.1/indexed_ubi"
    widget._inputGrainDataUrl.setText(grainURL)
    widget._inputGrainDataUrl.editingFinished.emit(grainURL)
    peaksURL = f"{dest_file}::/1.1/intensity_filtered_inner_peaks"
    widget._inputStrongFilteredPeaksDataUrl.setText(peaksURL)
    widget._inputStrongFilteredPeaksDataUrl.editingFinished.emit(peaksURL)
    latticeFile = "/data/projects/id03_3dxrd/expt/PROCESSED_DATA/Fe.par"
    widget._latticeParFile.setText(latticeFile)
    widget._latticeParFile.editingFinished.emit()
    widget._overwrite.setChecked(True)
    taskInputs = widget.get_task_inputs()
    assert taskInputs["folder_file_config"]["omega_motor"] == "diffrz"
    assert taskInputs["folder_file_config"]["scan_number"] == 1
    assert taskInputs["folder_file_config"]["master_file"] == master_file
    assert taskInputs["intensity_filtered_data_url"] == peaksURL
    assert taskInputs["lattice_file"] == latticeFile
