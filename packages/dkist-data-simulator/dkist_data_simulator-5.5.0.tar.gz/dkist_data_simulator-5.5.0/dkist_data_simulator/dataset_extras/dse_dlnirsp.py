from itertools import chain

from .dse_core import (
    DatasetExtraBase,
    DatasetExtraName,
    DatasetExtraTables,
    InstrumentTables,
)

DLNIRSP_DEFAULT_KEEP_SCHEMAS = [
    DatasetExtraTables.aggregate,
    DatasetExtraTables.common,
    DatasetExtraTables.fits,
    DatasetExtraTables.gos,
    DatasetExtraTables.ip_task,
]


class DlnirspDatasetExtra(DatasetExtraBase):
    def __init__(self, keep_schemas=None, **kwargs):
        instrument = InstrumentTables.dlnirsp
        if keep_schemas is None:
            keep_schemas = DLNIRSP_DEFAULT_KEEP_SCHEMAS
        super().__init__(instrument=instrument, keep_schemas=keep_schemas, **kwargs)


class DlnirspBadPixelMapExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.bad_pixel_map,
            dataset_shape=(1, 400, 70, 50),
            array_shape=(400, 70, 50),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.gos,
                DatasetExtraTables.aggregate,
            ],
        )


class DlnirspDarkExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.dark,
            dataset_shape=(1, 2048, 2048),
            array_shape=(2048, 2048),
        )


class DlnirspSolarGainExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.solar_gain,
            dataset_shape=(1, 2048, 2048),
            array_shape=(2048, 2048),
        )


class DlnirspCharacteristicSpectraExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.characteristic_spectra,
            dataset_shape=(1, 100),
            array_shape=(100,),
        )


class DlnirspSpectralCurvatureShiftsExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.spectral_curvature_shifts,
            dataset_shape=(1, 2, 10000),
            array_shape=(2, 10000),
        )


class DlnirspSpectralCurvatureScalesExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.spectral_curvature_scales,
            dataset_shape=(1, 2, 10000),
            array_shape=(2, 10000),
        )


class DlnirspWaveCalInputSpectrumExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.wavelength_calibration_input_spectrum,
            dataset_shape=(1, 100),
            array_shape=(100,),
        )


class DlnirspWaveCalReferenceSpectrumExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.wavelength_calibration_reference_spectrum,
            dataset_shape=(1, 10, 10),
            array_shape=(10, 10),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.atlas,
            ],
            remove_instrument_table=True,
        )


class DlnirspReferenceWavelengthVectorExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.reference_wavelength_vector,
            dataset_shape=(1, 1024),
            array_shape=(1024,),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.wavecal,
            ],
            remove_instrument_table=True,
        )


class DlnirspDemodulationMatricesExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.demodulation_matrices,
            dataset_shape=(1, 2048, 2048, 4, 8),
            array_shape=(2048, 2048, 4, 8),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.aggregate,
            ],
        )


class DlnirspPolcalAsScienceExtra(DlnirspDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.polcal_as_science,
            dataset_shape=(56, 400, 70, 50),
            array_shape=(400, 70, 50),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.gos,
            ],
        )


ALL_DLNIRSP_DATASET_EXTRAS = [
    DlnirspBadPixelMapExtra,
    DlnirspDarkExtra,
    DlnirspSolarGainExtra,
    DlnirspCharacteristicSpectraExtra,
    DlnirspSpectralCurvatureScalesExtra,
    DlnirspSpectralCurvatureShiftsExtra,
    DlnirspWaveCalInputSpectrumExtra,
    DlnirspWaveCalReferenceSpectrumExtra,
    DlnirspReferenceWavelengthVectorExtra,
    DlnirspDemodulationMatricesExtra,
    DlnirspPolcalAsScienceExtra,
]


def all_dlnirsp_dataset_extras():
    """Returns a file-by-file iterable for the dataset extras."""
    return chain.from_iterable([extra() for extra in ALL_DLNIRSP_DATASET_EXTRAS])
