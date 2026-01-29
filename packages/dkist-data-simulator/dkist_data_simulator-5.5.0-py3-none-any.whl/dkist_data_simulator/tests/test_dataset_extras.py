from collections import defaultdict

import pytest

from dkist_data_simulator.dataset_extras.dse_core import (
    DatasetExtraBase,
    DatasetExtraName,
    DatasetExtraSchema,
    DatasetExtraTables,
    InstrumentTables,
)
from dkist_data_simulator.dataset_extras.dse_cryo import (
    ALL_CRYO_DATASET_EXTRAS,
    CryoDatasetExtra,
    all_cryo_dataset_extras,
)
from dkist_data_simulator.dataset_extras.dse_dlnirsp import (
    ALL_DLNIRSP_DATASET_EXTRAS,
    all_dlnirsp_dataset_extras,
)
from dkist_data_simulator.dataset_extras.dse_visp import (
    ALL_VISP_DATASET_EXTRAS,
    VispDatasetExtra,
    all_visp_dataset_extras,
)


@pytest.mark.parametrize(
    "keep_schemas",
    [
        pytest.param([DatasetExtraTables.fits], id="fits_schema_only"),
        pytest.param(None, id="no_keep_schemas"),
    ],
)
@pytest.mark.parametrize(
    "required_only",
    [
        pytest.param(True, id="required_only"),
        pytest.param(False, id="not_required_only"),
    ],
)
@pytest.mark.parametrize(
    "instrument, remove_instrument_table",
    [
        pytest.param(InstrumentTables.visp, False, id="visp"),
        pytest.param(InstrumentTables.cryonirsp, False, id="cryonirsp"),
        pytest.param(InstrumentTables.dlnirsp, False, id="dlnirsp"),
        pytest.param(None, False, id="no_inst"),
        pytest.param(None, True, id="remove_inst_table"),
    ],
)
def test_dataset_extra_schema(
    required_only, instrument, remove_instrument_table, keep_schemas
):
    """
    Given: an instrument
    When: generating a dataset extra schema header with keywords
    Then: the correct keys are present and the incorrect keys are not present
    """
    schema = DatasetExtraSchema(
        instrument=instrument,
        keep_schemas=keep_schemas,
        remove_instrument_table=remove_instrument_table,
    )
    header = schema.generate(required_only=required_only)

    if required_only or keep_schemas is not None:
        assert "TTBLTRCK" not in header  # random non-required key in common table
    else:
        assert "TTBLTRCK" in header
        if instrument and not remove_instrument_table:
            match instrument.value:
                case "VISP":
                    assert "VSPARMID" in header
                    assert "CNARMID" not in header
                    assert "DLARMID" not in header
                case "CRYO-NIRSP":
                    assert "VSPARMID" not in header
                    assert "CNARMID" in header
                    assert "DLARMID" not in header
                case "DL-NIRSP":
                    assert "VSPARMID" not in header
                    assert "CNARMID" not in header
                    assert "DLARMID" in header
                case _:
                    raise ValueError("No valid instrument found")
        elif remove_instrument_table:
            assert "VSPARMID" not in header
            assert "CNARMID" not in header
            assert "DLARMID" not in header
        else:
            assert "VSPARMID" in header
            assert "CNARMID" in header
            assert "DLARMID" in header


@pytest.mark.parametrize(
    "dataset_extra_name",
    [
        pytest.param(DatasetExtraName.dark, id="dark_name"),
        pytest.param(None, id="no_extra_name"),
    ],
)
@pytest.mark.parametrize(
    "keep_schemas",
    [
        pytest.param(
            [
                DatasetExtraTables.ip_task,
                DatasetExtraTables.fits,
                DatasetExtraTables.common,
            ],
            id="iptask_schema",
        ),
        pytest.param(None, id="no_schema"),
    ],
)
def test_dataset_extra_base(dataset_extra_name, keep_schemas):
    """
    Given: ViSP with optional dataset_extra_name and/or optional schema table to keep
    When: generating a default shape dataset extra Dataset
    Then: the correct keys are present and the incorrect keys are not present
    """

    ds = DatasetExtraBase(
        instrument=InstrumentTables.visp,
        keep_schemas=keep_schemas,
        dataset_extra_name=dataset_extra_name,
    )
    headers = ds.generate_headers()
    for h in headers:
        assert h["PROCTYPE"] == "L1_EXTRA"
        assert h["NAXIS"] == 2
        assert h["NAXIS1"] == 10
        assert h["NAXIS2"] == 5
        assert "NAXIS3" not in h
        assert h["INSTRUME"] == "VISP"
        assert "VSPARMID" in h
        assert "CNARMID" not in h
        assert "DLARMID" not in h
        if dataset_extra_name:
            assert h["EXTNAME"] == dataset_extra_name
        if keep_schemas:
            assert "IPTASK" in h  # iptask table
            assert "AVGLLVL" not in h  # aggregate table
            assert "LVL0STAT" not in h  # gos table
        else:
            assert "IPTASK" in h  # iptask table
            assert "AVGLLVL" in h  # aggregate table
            assert "LVL0STAT" in h  # gos table


@pytest.mark.parametrize(
    "dataset_extra_cls",
    [
        pytest.param(extra, id=extra.__name__)
        for extra in ALL_VISP_DATASET_EXTRAS
        + ALL_CRYO_DATASET_EXTRAS
        + ALL_DLNIRSP_DATASET_EXTRAS
    ],
)
def test_dataset_extra_each_instrument(dataset_extra_cls):
    """
    Given: an instrument
    When: making each of the pre-defined dataset extras for that instrument
    Then: the header contains the correct names and the dataset is the correct shape
    """
    ds = dataset_extra_cls()
    assert ds.array_shape == ds.data_shape
    assert ds.n_files == ds.dataset_shape[0]
    for d in ds:
        header = d.header()
        assert header["INSTRUME"] == ds.instrument
        assert header["EXTNAME"] == ds.dataset_extra_name
        assert d.data.shape == ds.array_shape


@pytest.mark.parametrize(
    "all_extras_function, total_files",
    [
        pytest.param(all_visp_dataset_extras, 93, id="visp"),
        pytest.param(all_cryo_dataset_extras, 74, id="cryonirsp"),
        pytest.param(all_dlnirsp_dataset_extras, 66, id="dlnirsp"),
    ],
)
def test_dataset_extra_instrument_combined(all_extras_function, total_files, tmpdir):
    """
    Given: an instrument
    When: making the all-dataset-extra iterable for that instrument
    Then: the iterable is the correct length
    """
    extras = all_extras_function()
    extra_iterations = defaultdict(int)
    extra_n_files = defaultdict(int)
    for dse in extras:
        extra_iterations[dse.dataset_extra_name] += 1
        extra_n_files[dse.dataset_extra_name] = dse.n_files
    assert extra_iterations == extra_n_files
    assert sum(extra_iterations.values()) == total_files


@pytest.mark.parametrize(
    "dataset_extra_cls, key",
    [
        pytest.param(VispDatasetExtra, "VSPBEAM", id="visp"),
        pytest.param(CryoDatasetExtra, "CNBEAM", id="cryo"),
    ],
)
def test_dataset_extra_multi_beam(dataset_extra_cls, key):
    """
    Given: an instrument with multiple beams
    When: making a dataset extra that has separate files for each beam
    Then: the beam id keys are set to increment correctly
    """
    ds = dataset_extra_cls()
    assert ds.n_files == 2
    beam_keys = [d.header()[key] for d in ds]
    assert beam_keys == [1, 2]


@pytest.mark.parametrize(
    "dataset_extra_cls, key",
    [
        pytest.param(VispDatasetExtra, "VSPBEAM", id="visp"),
        pytest.param(CryoDatasetExtra, "CNBEAM", id="cryo"),
    ],
)
def test_dataset_extra_reference_no_beam(dataset_extra_cls, key):
    """
    Given: an instrument with multiple beams
    When: making a reference dataset extra that has no instrument section
    Then: the beam id keys are not present in the header
    """
    ds = dataset_extra_cls(remove_instrument_table=True)
    with pytest.raises(KeyError):
        [d.header()[key] for d in ds]
