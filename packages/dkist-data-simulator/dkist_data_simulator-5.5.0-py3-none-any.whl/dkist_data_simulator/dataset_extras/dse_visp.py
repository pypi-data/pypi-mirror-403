from itertools import chain

from .dse_core import (
    DatasetExtraBase,
    DatasetExtraName,
    DatasetExtraTables,
    InstrumentTables,
)

VISP_DEFAULT_KEEP_SCHEMAS = [
    DatasetExtraTables.aggregate,
    DatasetExtraTables.common,
    DatasetExtraTables.fits,
    DatasetExtraTables.gos,
    DatasetExtraTables.ip_task,
]


class VispDatasetExtra(DatasetExtraBase):
    def __init__(self, keep_schemas=None, remove_instrument_table=False, **kwargs):
        instrument = InstrumentTables.visp
        if keep_schemas is None:
            keep_schemas = VISP_DEFAULT_KEEP_SCHEMAS

        super().__init__(
            instrument=instrument,
            keep_schemas=keep_schemas,
            remove_instrument_table=remove_instrument_table,
            **kwargs
        )

        if not remove_instrument_table:
            self.add_generator_function("VSPBEAM", type(self).beam_number)

    def beam_number(self, key: str):
        return self.index + 1


class VispDarkExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.dark,
            dataset_shape=(2, 1000, 2560),
            array_shape=(1000, 2560),
        )


class VispBackgroundLightExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.background_light,
            dataset_shape=(2, 1000, 2560),
            array_shape=(1000, 2560),
        )


class VispSolarGainExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.solar_gain,
            dataset_shape=(2, 1000, 2560),
            array_shape=(1000, 2560),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
            ],
        )


class VispCharacteristicSpectraExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.characteristic_spectra,
            dataset_shape=(2, 1000, 2560),
            array_shape=(1000, 2560),
        )


class VispModulationStateOffsetsExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.modulation_state_offsets,
            dataset_shape=(20, 2),
            array_shape=(2,),
        )


class VispBeamAnglesExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.beam_angles,
            dataset_shape=(2, 1),
            array_shape=(1,),
        )


class VispSpectralCurvatureShiftsExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.spectral_curvature_shifts,
            dataset_shape=(2, 2560),
            array_shape=(2560,),
        )


class VispWaveCalInputSpectrumExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.wavelength_calibration_input_spectrum,
            dataset_shape=(1, 1000),
            array_shape=(1000,),
        )
        self.add_constant_key("VSPBEAM", 1)


class VispWaveCalReferenceSpectrumExtra(VispDatasetExtra):
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


class VispReferenceWavelengthVectorExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.reference_wavelength_vector,
            dataset_shape=(1, 1000),
            array_shape=(1000,),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.wavecal,
            ],
            remove_instrument_table=True,
        )


class VispDemodulationMatricesExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.demodulation_matrices,
            dataset_shape=(2, 1000, 2560, 4, 10),
            array_shape=(1000, 2560, 4, 10),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.aggregate,
            ],
        )


class VispPolcalAsScienceExtra(VispDatasetExtra):
    def __init__(self):
        super().__init__(
            dataset_extra_name=DatasetExtraName.polcal_as_science,
            dataset_shape=(56, 1000, 2560),
            array_shape=(1000, 2560),
            keep_schemas=[
                DatasetExtraTables.common,
                DatasetExtraTables.fits,
                DatasetExtraTables.ip_task,
                DatasetExtraTables.gos,
            ],
        )


ALL_VISP_DATASET_EXTRAS = [
    VispDarkExtra,
    VispBackgroundLightExtra,
    VispSolarGainExtra,
    VispCharacteristicSpectraExtra,
    VispModulationStateOffsetsExtra,
    VispBeamAnglesExtra,
    VispSpectralCurvatureShiftsExtra,
    VispWaveCalInputSpectrumExtra,
    VispWaveCalReferenceSpectrumExtra,
    VispReferenceWavelengthVectorExtra,
    VispDemodulationMatricesExtra,
    VispPolcalAsScienceExtra,
]


def all_visp_dataset_extras():
    """Returns a file-by-file iterable for the dataset extras."""
    return chain.from_iterable([extra() for extra in ALL_VISP_DATASET_EXTRAS])
