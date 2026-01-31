from orangecontrib.ewoks3dxrd.image_file_generator import OWImageFileGenerator


def test_correction_image_widget(qtapp):  # noqa F401
    widget = OWImageFileGenerator()

    raw_master_file = "/data/projects/id03_3dxrd/calibration/Si_cube_id03/RAW_DATA/3DXRD_calibration/3DXRD_calibration_si_xtal_bkg/3DXRD_calibration_si_xtal_bkg.h5"
    widget._folderGroup._masterFilePath.setText(
        file_path=raw_master_file,
    )
    widget._plotImageWidget.setBackend(backend="matplotlib")
    widget._folderGroup._masterFilePath._lineEdit.editingFinished.emit()
    widget._folderGroup._masterFilePath.sigMasterFileChanged.emit(raw_master_file)
    parms = widget._folderGroup.getConfig()
    assert parms["master_file_path"] == raw_master_file
    assert parms["scan_number"] == 1
    assert parms["detector"] == "frelon1"
