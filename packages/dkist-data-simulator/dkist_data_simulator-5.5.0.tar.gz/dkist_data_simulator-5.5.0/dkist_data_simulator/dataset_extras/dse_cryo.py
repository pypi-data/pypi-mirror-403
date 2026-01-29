from itertools import chain

from .dse_core import (
    DatasetExtraBase,
    DatasetExtraName,
    DatasetExtraTables,
    InstrumentTables,
)

CRYO_DEFAULT_KEEP_SCHEMAS = [
    DatasetExtraTables.aggregate,
    DatasetExtraTables.common,
    DatasetExtraTables.fits,
    DatasetExtraTables.gos,
    DatasetExtraTables.ip_task,
]


class CryoDatasetExtra(DatasetExtraBase):
    def __init__(self, keep_schemas=None, remove_instrument_table=False, **kwargs):
        instrument = InstrumentTables.cryonirsp
        if keep_schemas is None:
            keep_schemas = CRYO_DEFAULT_KEEP_SCHEMAS

        super().__init__(
            instrument=instrument,
            keep_schemas=keep_schemas,
            remove_instrument_table=remove_instrument_table,
            **kwargs
        )

        if not remove_instrument_table:
            self.add_generator_function("CNBEAM", type(self).beam_number)

    def beam_number(self, key: str):
        return self.index + 1


class CryoBadPixelMapExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.bad_pixel_map,
            dataset_shape=(1, 2048, 2048),
            array_shape=(2048, 2048),
        )


class CryoDarkExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.dark,
            dataset_shape=(2, 2048, 2048),
            array_shape=(2048, 2048),
        )


class CryoSolarGainExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.solar_gain,
            dataset_shape=(2, 2048, 2048),
            array_shape=(2048, 2048),
        )


class CryoCharacteristicSpectraExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.characteristic_spectra,
            dataset_shape=(2, 2048),
            array_shape=(2048,),
        )


class CryoBeamOffsetsExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.beam_offsets,
            dataset_shape=(2, 2),
            array_shape=(2,),
        )


class CryoBeamAnglesExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.beam_angles,
            dataset_shape=(2, 1),
            array_shape=(1,),
        )


class CryoSpectralCurvatureShiftsExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.spectral_curvature_shifts,
            dataset_shape=(2, 2048),
            array_shape=(2048,),
        )


class CryoWaveCalInputSpectrumExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.wavelength_calibration_input_spectrum,
            dataset_shape=(1, 1024),
            array_shape=(1024,),
        )


class CryoWaveCalReferenceSpectrumExtra(CryoDatasetExtra):
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


class CryoReferenceWavelengthVectorExtra(CryoDatasetExtra):
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


class CryoDemodulationMatricesExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.demodulation_matrices,
            dataset_shape=(2, 4, 8),
            array_shape=(4, 8),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.aggregate,
            ],
        )


class CryoPolcalAsScienceExtra(CryoDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.polcal_as_science,
            dataset_shape=(56, 2046, 2048),
            array_shape=(2046, 2048),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.gos,
            ],
        )


ALL_CRYO_DATASET_EXTRAS = [
    CryoBadPixelMapExtra,
    CryoDarkExtra,
    CryoSolarGainExtra,
    CryoCharacteristicSpectraExtra,
    CryoBeamOffsetsExtra,
    CryoBeamAnglesExtra,
    CryoSpectralCurvatureShiftsExtra,
    CryoWaveCalInputSpectrumExtra,
    CryoWaveCalReferenceSpectrumExtra,
    CryoReferenceWavelengthVectorExtra,
    CryoDemodulationMatricesExtra,
    CryoPolcalAsScienceExtra,
]


def all_cryo_dataset_extras():
    """Returns a file-by-file iterable for the dataset extras."""
    return chain.from_iterable([extra() for extra in ALL_CRYO_DATASET_EXTRAS])
