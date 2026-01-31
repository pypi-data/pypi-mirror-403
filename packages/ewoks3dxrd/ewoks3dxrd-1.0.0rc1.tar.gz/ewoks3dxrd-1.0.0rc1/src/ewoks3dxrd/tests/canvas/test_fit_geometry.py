from orangecontrib.ewoks3dxrd.fit_geometry import OWFitGeometry


def test_fit_geometry(qtapp):  # noqa F401
    widget = OWFitGeometry()
    widget._latticeGroup._latticeParFile.setText(
        "/data/projects/id03_3dxrd/id03_expt/PROCESSED_DATA/Si-Silicon.cif"
    )
    widget._settingsPanel._geometryFileWidget.setText(
        "/data/projects/id03_3dxrd/calibration/example_notebooks/geometry.par"
    )
    widget._plot.setBackend(backend="matplotlib")
    widget._columnURLBox._url.setText(
        "/data/projects/id03_3dxrd/calib_dataset/3DXRD_calibration_si_xtal.h5::/1.1/spatial_corrected_peaks"
    )
    assert widget._peaksColumnFile is not None
