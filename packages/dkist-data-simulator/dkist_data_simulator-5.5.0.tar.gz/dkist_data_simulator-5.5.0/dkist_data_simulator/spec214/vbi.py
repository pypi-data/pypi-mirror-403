from typing import Literal

import astropy.units as u
import numpy as np
from astropy.wcs import WCS
from sunpy.util.decorators import cached_property_based_on

from dkist_data_simulator.dataset import key_function
from dkist_data_simulator.spec214.core import Spec214Dataset, TimeVaryingWCSGenerator


class BaseVBIDataset(Spec214Dataset):
    """
    A base class for VBI datasets.
    """

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        detector_shape=(4096, 4096),
        vbi_camera: Literal["red", "blue", "red-all"] = "red",
        mosaic: bool = False,
    ):
        match vbi_camera.lower():
            case "blue":
                n_pos = 9
                self.step_pattern = [5, 6, 3, 2, 1, 4, 7, 8, 9]
                self.plate_scale = 0.011 * u.arcsec / u.pix
                # fmt: off
                self.mindices_of_field_pos = ["index_placeholder",
                       (1, 3), (2, 3), (3, 3),
                       (1, 2), (2, 2), (3, 2),
                       (1, 1), (2, 1), (3, 1),
                       ]
                # fmt: on
            case "red":
                n_pos = 4
                self.step_pattern = [1, 2, 4, 3]
                self.plate_scale = 0.0169 * u.arcsec / u.pix
                # fmt: off
                self.mindices_of_field_pos = ["index_placeholder",
                      (1, 2), (2, 2),
                      (1, 1), (2, 1),
                      ]
                # fmt: on
            case "red-all":
                n_pos = 5
                self.step_pattern = [1, 2, 4, 3, 5]
                self.plate_scale = 0.0169 * u.arcsec / u.pix
                self.mindices_of_field_pos = [
                    "index_placeholder",
                    (1, 3),
                    (3, 3),
                    (1, 1),
                    (3, 1),
                    (2, 2),
                ]
            case _:
                raise ValueError(f"{vbi_camera = } is not a valid VBI camera option")

        if not mosaic:
            n_pos = 1
            self.step_pattern = [5]
            self.mindices_of_field_pos = ["index_placeholder"] * 5 + [(1, 1)]

        self.mosaic = mosaic
        self.n_pos = n_pos
        self.n_time = n_time

        array_shape = tuple(detector_shape)
        if n_time > 1:
            dataset_shape_rev = (*detector_shape, n_time)
        else:
            dataset_shape_rev = tuple(detector_shape)

        super().__init__(
            dataset_shape_rev[::-1],
            array_shape,
            time_delta=time_delta,
            instrument="vbi",
        )
        self.files_shape = (*self.files_shape, n_pos)
        self.files_ndim = len(self.files_shape)
        self.n_files = int(np.prod(self.files_shape))

        self.add_constant_key("DTYPE1", "SPATIAL")
        self.add_constant_key("DTYPE2", "SPATIAL")
        self.add_constant_key("DPNAME1", "spatial x")
        self.add_constant_key("DPNAME2", "spatial y")
        self.add_constant_key("DWNAME1", "helioprojective longitude")
        self.add_constant_key("DWNAME2", "helioprojective latitude")
        self.add_constant_key("DUNIT1", "arcsec")
        self.add_constant_key("DUNIT2", "arcsec")
        self.add_constant_key("LINEWAV", linewave.to_value(u.nm))
        self.add_constant_key("VBINSTP", self.n_pos)
        self.add_constant_key("VBISTPAT", ",".join([str(i) for i in self.step_pattern]))

        if n_time > 1:
            self.add_constant_key("DTYPE3", "TEMPORAL")
            self.add_constant_key("DPNAME3", "frame number")
            self.add_constant_key("DWNAME3", "time")
            self.add_constant_key("DUNIT3", "s")

    @property
    def current_camera_pos(self) -> int:
        if self.n_time > 1:
            return self.file_index[1] + 1
        else:
            return self.file_index[0] + 1

    @property
    def current_mosaic_field_position(self) -> int:
        return self.step_pattern[self.current_camera_pos - 1]

    @property
    def current_dsps_repeat(self) -> int:
        if self.n_time > 1:
            return self.file_index[0]
        else:
            return 0

    @property
    def data(self):
        return np.random.random(self.array_shape)


class SimpleVBIDataset(BaseVBIDataset):
    """
    A simple VBI dataset with a HPC grid aligned to the pixel axes.
    """

    name = "vbi-simple"

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        detector_shape=(4096, 4096),
        vbi_camera: Literal["red", "blue"] = "red",
    ):
        super().__init__(
            n_time,
            time_delta,
            linewave=linewave,
            detector_shape=detector_shape,
            vbi_camera=vbi_camera,
            mosaic=False,
        )

    @property
    def fits_wcs(self):
        if self.array_ndim != 2:
            raise ValueError("VBI dataset generator expects two dimensional FITS WCS.")

        w = WCS(naxis=self.array_ndim)
        w.wcs.crpix = self.array_shape[1] / 2, self.array_shape[0] / 2
        w.wcs.crval = 0, 0
        w.wcs.cdelt = [self.plate_scale.to_value(u.arcsec / u.pix) for i in range(2)]
        w.wcs.cunit = "arcsec", "arcsec"
        w.wcs.ctype = "HPLN-TAN", "HPLT-TAN"
        w.wcs.pc = np.identity(self.array_ndim)
        return w


class MosaicedVBIDataset(BaseVBIDataset):
    """
    A mosaik'd dataset with correct mosaic index keys and WCS values
    """

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        vbi_camera,
        detector_shape=(4096, 4096),
    ):
        super().__init__(
            n_time,
            time_delta,
            linewave=linewave,
            vbi_camera=vbi_camera,
            mosaic=True,
            detector_shape=detector_shape,
        )

        # Kind of nasty to hardcode this, but whatever
        # Taken from Blue data taken on May 11th, 2021
        self.CRVALs_by_position = {
            1: (-0.008249197036196473, -0.0006135090889007315),
            2: (-0.002317657297546805, -0.0001723610794093499),
            3: (-0.00628512107866833, -0.0004674396171848149),
            4: (-0.004281763497165903, -0.0003184451268690273),
            5: (-0.004281746141954696, -0.0003184443597246071),
            6: (-0.004321040295000408, -0.0003213684050815774),
            7: (-0.0003535952015734776, -2.629428697388573e-05),
            8: (-0.002356942994829349, -0.0001752814836928538),
            9: (-0.006245898142674184, -0.0004645083011308958),
        }
        self.CRPIXs_by_position = {
            1: (4271.916665454963, 4156.592392327204),  # M, M
            2: (880.2500395909186, 4156.592392327204),  # L, M
            3: (880.250039438403, 756.5922702407024),  # L, B
            4: (4271.916665454963, 756.5922702299208),  # M, B
            5: (7663.583169381011, 756.5922702423875),  # R, B
            6: (7663.583169379749, 4156.592392309716),  # R, M
            7: (7663.583169508412, 7556.592392317916),  # R, T
            8: (4271.916665575761, 7556.592392330609),  # M, T
            9: (880.250039413763, 7556.5923923026385),  # L, T
        }

    @property
    @cached_property_based_on("index")
    def fits_wcs(self) -> WCS:
        w = WCS(naxis=self.array_ndim)
        w.wcs.crpix = self.CRPIXs_by_position[self.current_camera_pos]
        w.wcs.crval = self.CRVALs_by_position[self.current_camera_pos]
        w.wcs.cdelt = [self.plate_scale.to_value(u.arcsec / u.pix) for _ in range(2)]
        w.wcs.cunit = "arcsec", "arcsec"
        w.wcs.ctype = "HPLN-TAN", "HPLT-TAN"
        w.wcs.pc = np.identity(self.array_ndim)
        return w

    @key_function(
        "MAXIS",
        "MAXIS1",
        "MAXIS2",
        "MINDEX1",
        "MINDEX2",
        "VBISTP",
    )
    def moasic_keys(self, key: str):
        match key:
            case "VBISTP":
                return int(self.current_camera_pos)
            case "MINDEX1":
                return self.mindices_of_field_pos[self.current_mosaic_field_position][0]
            case "MINDEX2":
                return self.mindices_of_field_pos[self.current_mosaic_field_position][1]

        match self.n_pos:
            case 4:
                axis_length = 2
            case 5 | 9:
                axis_length = 3
            case _:
                raise ValueError(
                    f"Number of camera positions ({self.n_pos}) doesn't match a mosaic we know about"
                )

        constant_keys = {
            "MAXIS": 2,
            "MAXIS1": axis_length,
            "MAXIS2": axis_length,
        }
        return constant_keys.get(key, super().moasic_keys(key))


class MosaicedVBIBlueDataset(MosaicedVBIDataset):
    """
    A mosaik'd VBI-BLUE dataset with correct mosaic index keys and real WCS values.
    """

    name = "vbi-mosaic-blue"

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        detector_shape=(4096, 4096),
    ):
        super().__init__(
            n_time,
            time_delta,
            linewave=linewave,
            vbi_camera="blue",
            detector_shape=detector_shape,
        )


class MosaicedVBIRedDataset(MosaicedVBIDataset):
    """
    A mosaik'd VBI-RED dataset with correct mosaic index keys and real WCS values.
    """

    name = "vbi-mosaic-red"

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        detector_shape=(4096, 4096),
    ):
        super().__init__(
            n_time,
            time_delta,
            linewave=linewave,
            vbi_camera="red",
            detector_shape=detector_shape,
        )


class MosaicedVBIRedAllDataset(MosaicedVBIDataset):
    """
    A mosaik'd VBI-RED dataset with correct mosaic index keys and real WCS values.
    """

    name = "vbi-mosaic-red-all"

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        detector_shape=(4096, 4096),
    ):
        super().__init__(
            n_time,
            time_delta,
            linewave=linewave,
            vbi_camera="red-all",
            detector_shape=detector_shape,
        )


class TimeDependentVBIDataset(SimpleVBIDataset):
    """
    A version of the VBI dataset where the CRVAL and PC matrix change with time.
    """

    name = "vbi-time-dependent"

    def __init__(
        self,
        n_time,
        time_delta,
        *,
        linewave,
        pointing_shift_rate=10 * u.arcsec / u.s,
        rotation_shift_rate=0.5 * u.deg / u.s,
        rotation_angle=-2 * u.deg,
        **kwargs,
    ):
        super().__init__(n_time, time_delta, linewave=linewave, **kwargs)

        self.wcs_generator = TimeVaryingWCSGenerator(
            crval=(0, 0),
            rotation_angle=rotation_angle,
            crpix=(self.array_shape[1] / 2, self.array_shape[0] / 2),
            cdelt=[self.plate_scale.to_value(u.arcsec / u.pix) for i in range(2)],
            pointing_shift_rate=u.Quantity([pointing_shift_rate, pointing_shift_rate]),
            rotation_shift_rate=rotation_shift_rate,
            jitter=False,
        )

    @property
    def fits_wcs(self):
        return self.wcs_generator.generate_wcs(self.time_index * self.time_delta * u.s)
