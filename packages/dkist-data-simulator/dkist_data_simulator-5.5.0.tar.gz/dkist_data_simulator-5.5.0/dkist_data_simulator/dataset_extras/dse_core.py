from enum import StrEnum
from typing import Any

import numpy as np
from astropy.io import fits
from dkist_fits_specifications import dataset_extras

from dkist_data_simulator.dataset import Dataset, key_function
from dkist_data_simulator.schemas import Schema
from dkist_data_simulator.spec122 import KNOWN_INSTRUMENT_TABLES

__all__ = [
    "DatasetExtraName",
    "DatasetExtraTables",
    "InstrumentTables",
    "DatasetExtraBase",
    "DatasetExtraSchema",
]


class DatasetExtraTables(StrEnum):
    aggregate = "aggregate"
    atlas = "atlas"
    common = "common"
    fits = "fits"
    gos = "gos"
    ip_task = "ip_task"
    wavecal = "wavecal"


InstrumentTables = StrEnum("InstrumentTables", KNOWN_INSTRUMENT_TABLES)

common_schema = dataset_extras.load_full_dataset_extra("common")["common"]
extname_values = common_schema["EXTNAME"]["values"]
DatasetExtraName = StrEnum(
    "DatasetExtraName", {s.lower().replace(" ", "_"): s for s in extname_values}
)


class DatasetExtraSchema(Schema):
    """
    A representation of the Dataset Extra schema.

    Parameters
    ----------
    instrument
        Member of `.InstrumentTables`.  If None, all instrument tables will be
        in the header.
    keep_schemas
        List of `.DatasetExtraTables` to keep in the headers.  If `None`, all
        dataset extra tables will be in the header.
    remove_instrument_table
        Set to true to remove the instrument table, relevant for certain
        reference dataset extras.  If True, no instrument tables will be
        in the header.
    random
        Instance of the Numpy random `Generator` class.  If None,
        `numpy.random.default_rng` is used.
    """

    def __init__(
        self,
        instrument: InstrumentTables | None = None,
        keep_schemas: list[DatasetExtraTables] | None = None,
        remove_instrument_table: bool = False,
        random=None,
        **header_values,
    ):
        random = random or np.random.default_rng()

        sections = dataset_extras.load_processed_dataset_extra(**header_values)
        sections.pop("compression", None)

        if instrument or remove_instrument_table:
            for inst_table in InstrumentTables:
                if inst_table != instrument or remove_instrument_table:
                    sections.pop(inst_table.name, None)
        if keep_schemas:
            for dse_table in DatasetExtraTables:
                if dse_table not in keep_schemas:
                    sections.pop(dse_table, None)

        super().__init__(self.sections_from_dicts(sections.values(), random=random))


class DatasetExtraBase(Dataset):
    """
    Generate a collection of FITS files for one instrument and one Dataset Extra type.

    Parameters
    ----------
    dataset_extra_name
        Member of `.DatasetExtraName` for the EXTNAME keyword.
    dataset_shape
        The full shape of the dataset.  For Dataset Extra files, this is normally
        ``(N, yshape, xshape)`` or ``(N, vshape)`` where ``N`` is the number of files
        to be generated and the remaining dimensions are the data size.
    array_shape
        The size of the data.  Because the dataset extras are not reconstructed into
        higher-dimensional arrays, array_shape should not include dummy dimensions.
        Arrays are ``(yshape, xshape)``, vectors are ``(vshape)``, and single values
        are ``(1,)``.
    instrument
        Member of `.InstrumentTables` passed to the Schema.  If None, all
        instrument tables will be in the header.
    keep_schemas
        List of `.DatasetExtraTables` to keep in the headers, passed to the
        Schema.  If None, all dataset extra tables will be in the header.
    remove_instrument_table
        Bool passed to the Schema. Set to True to remove the instrument table,
        which is relevant for certain reference dataset extras.  If True, no
        instrument tables will be in the header.
    random
        Instance of the Numpy random `Generator` class passed to Schema.  If
        None, `numpy.random.default_rng` is used.
    """

    def __init__(
        self,
        dataset_extra_name: DatasetExtraName | None = None,
        dataset_shape: tuple[int, ...] = (2, 5, 10),
        array_shape: tuple[int, ...] = (5, 10),
        instrument: InstrumentTables | None = None,
        keep_schemas: list[DatasetExtraTables] | None = None,
        remove_instrument_table: bool = False,
        random=None,
        **schema_header_values: dict[str, Any] | fits.Header,
    ):
        # Calculation for the Schema to expand:
        naxis = len(array_shape)
        # Override any of the defaults with **schema_header_values
        full_input_header = {
            "NAXIS": naxis,
            **schema_header_values,
        }
        self.file_schema = DatasetExtraSchema(
            instrument=instrument,
            keep_schemas=keep_schemas,
            remove_instrument_table=remove_instrument_table,
            random=random,
            **full_input_header,
        )
        self.dataset_extra_name = dataset_extra_name
        self.instrument = instrument
        super().__init__(
            file_schema=self.file_schema,
            dataset_shape=dataset_shape,
            array_shape=array_shape,
        )

        self.add_constant_key("NAXIS", self.array_ndim)
        self.add_constant_key("TIMESYS", "UTC")
        self.add_constant_key("ORIGIN", "National Solar Observatory")
        self.add_constant_key("TELESCOP", "Daniel K. Inouye Solar Telescope")
        self.add_constant_key("OBSRVTRY", "Haleakala High Altitude Observatory Site")
        self.add_constant_key("NETWORK", "NSF-DKIST")
        self.add_constant_key("BUNIT", "ADU")
        self.add_constant_key("PROCTYPE", "L1_EXTRA")
        if self.instrument:
            self.add_constant_key("INSTRUME", self.instrument.value)
        if self.dataset_extra_name:
            self.add_constant_key("EXTNAME", self.dataset_extra_name.value)

    @property
    def data(self):
        return np.zeros(self.array_shape)

    @key_function("NAXIS<n>")
    def naxis(self, key: str):
        fits_ind = int(key[-1])
        ind = self.array_ndim - fits_ind
        return self.array_shape[ind]
