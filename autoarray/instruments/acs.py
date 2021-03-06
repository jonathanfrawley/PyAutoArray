from autoarray.structures.arrays import abstract_array
from autoarray.structures.arrays.two_d import array_2d_util
from autoarray.structures.arrays.two_d import array_2d
from autoarray.layout import layout as lo, layout_util
from autoarray.layout import region as reg
from autoarray import exc

from astropy.io import fits

import shutil
import os

import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel("INFO")


def fits_hdu_from_quadrant_letter(quadrant_letter):

    if quadrant_letter == "A" or quadrant_letter == "B":
        return 1
    elif quadrant_letter == "C" or quadrant_letter == "D":
        return 4
    else:
        raise exc.FrameException("Quadrant letter for FrameACS must be A, B, C or D.")


def array_eps_to_counts(array_eps, bscale, bzero):

    if bscale is None:
        raise exc.FrameException(
            "Cannot convert a Frame2D to units COUNTS without a bscale attribute (bscale = None)."
        )

    return (array_eps - bzero) / bscale


class Array2DACS(array_2d.Array2D):
    """
    An ACS array consists of four quadrants ('A', 'B', 'C', 'D') which have the following layout:

       <--------S-----------   ---------S----------->
    [] [========= 2 =========] [========= 3 =========] []          /\
    /    [xxxxxxxxxxxxxxxxxxxxx] [xxxxxxxxxxxxxxxxxxxxx]  /        |
    |   [xxxxxxxxxxxxxxxxxxxxx] [xxxxxxxxxxxxxxxxxxxxx]  |         | Direction arctic
    P   [xxxxxxxxx B/C xxxxxxx] [xxxxxxxxx A/D xxxxxxx]  P         | clocks an image
    |   [xxxxxxxxxxxxxxxxxxxxx] [xxxxxxxxxxxxxxxxxxxxx]  |         | without any rotation
    \/  [xxxxxxxxxxxxxxxxxxxxx] [xxxxxxxxxxxxxxxxxxxxx]  \/        | (e.g. towards row 0
                                                                   | of the NumPy arrays)

    For a ACS .fits file:

    - The images contained in hdu 1 correspond to quadrants B (left) and A (right).
    - The images contained in hdu 4 correspond to quadrants C (left) and D (right).
    """

    @classmethod
    def from_fits(cls, file_path, quadrant_letter):
        """
        Use the input .fits file and quadrant letter to extract the quadrant from the full CCD, perform
        the rotations required to give correct arctic clocking and convert the image from units of COUNTS / CPS to
        ELECTRONS.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """

        hdu = fits_hdu_from_quadrant_letter(quadrant_letter=quadrant_letter)

        array = array_2d_util.numpy_array_2d_from_fits(file_path=file_path, hdu=hdu)

        return cls.from_ccd(array_electrons=array, quadrant_letter=quadrant_letter)

    @classmethod
    def from_ccd(
        cls,
        array_electrons,
        quadrant_letter,
        parallel_size=2068,
        serial_size=2072,
        exposure_info=None,
    ):
        """
        Using an input array of both quadrants in electrons, use the quadrant letter to extract the quadrant from the
        full CCD and perform the rotations required to give correct arctic.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """
        if quadrant_letter == "B" or quadrant_letter == "C":

            return cls.left(
                array_electrons=array_electrons[0:parallel_size, 0:serial_size],
                exposure_info=exposure_info,
            )
        elif quadrant_letter == "A" or quadrant_letter == "D":
            return cls.right(
                array_electrons=array_electrons[
                    0:parallel_size, serial_size : serial_size * 2
                ],
                exposure_info=exposure_info,
            )
        else:
            raise exc.FrameException(
                "Quadrant letter for FrameACS must be A, B, C or D."
            )

    @classmethod
    def left(cls, array_electrons, exposure_info=None):
        """
        Use an input array of the left quadrant in electrons and perform the rotations required to give correct
        arctic clocking.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """

        array_electrons = layout_util.rotate_array_from_roe_corner(
            array=array_electrons, roe_corner=(1, 0)
        )

        return cls.manual(
            array=array_electrons, exposure_info=exposure_info, pixel_scales=0.05
        )

    @classmethod
    def right(cls, array_electrons, exposure_info=None):
        """
        Use an input array of the right quadrant in electrons and perform the rotations required to give correct
        arctic clocking.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """

        array_electrons = layout_util.rotate_array_from_roe_corner(
            array=array_electrons, roe_corner=(1, 1)
        )

        return cls.manual(
            array=array_electrons, exposure_info=exposure_info, pixel_scales=0.05
        )

    def update_fits(self, original_file_path, new_file_path):
        """
        Output the array to a .fits file.

        Parameters
        ----------
        file_path : str
            The path the file is output to, including the filename and the ``.fits`` extension,
            e.g. '/path/to/filename.fits'
        overwrite : bool
            If a file already exists at the path, if overwrite=True it is overwritten else an error is raised."""

        new_file_dir = os.path.split(new_file_path)[0]

        if not os.path.exists(new_file_dir):

            os.makedirs(new_file_dir)

        if not os.path.exists(new_file_path):

            shutil.copy(original_file_path, new_file_path)

        hdulist = fits.open(new_file_path)

        hdulist[self.exposure_info.hdu].data = self.layout.original_orientation_from(
            array=self
        )

        ext_header = hdulist[4].header
        bscale = ext_header["BSCALE"]

        os.remove(new_file_path)

        hdulist.writeto(new_file_path)


class ImageACS(Array2DACS):
    """
    The layout of an ACS array and image is given in `FrameACS`.

    This class handles specifically the image of an ACS observation, assuming that it contains specific
    header info.
    """

    @classmethod
    def from_fits(cls, file_path, quadrant_letter):
        """
        Use the input .fits file and quadrant letter to extract the quadrant from the full CCD, perform
        the rotations required to give correct arctic clocking and convert the image from units of COUNTS / CPS to
        ELECTRONS.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """

        hdu = fits_hdu_from_quadrant_letter(quadrant_letter=quadrant_letter)

        exposure_info = cls.exposure_info_from_fits(file_path=file_path, hdu=hdu)

        array = cls.array_converted_to_electrons_from_fits(
            file_path=file_path, hdu=hdu, exposure_info=exposure_info
        )

        return cls.from_ccd(
            array_electrons=array,
            quadrant_letter=quadrant_letter,
            exposure_info=exposure_info,
        )

    @staticmethod
    def exposure_info_from_fits(file_path, hdu):

        hdulist = fits.open(file_path)

        sci_header = hdulist[0].header

        exposure_time = sci_header["EXPTIME"]
        date_of_observation = sci_header["DATE-OBS"]
        time_of_observation = sci_header["TIME-OBS"]

        ext_header = hdulist[hdu].header

        units = ext_header["BUNIT"]
        bscale = ext_header["BSCALE"]
        bzero = ext_header["BZERO"]

        return ExposureInfoACS(
            exposure_time=exposure_time,
            date_of_observation=date_of_observation,
            time_of_observation=time_of_observation,
            original_units=units,
            bscale=bscale,
            bzero=bzero,
            hdu=hdu,
        )

    @staticmethod
    def array_converted_to_electrons_from_fits(file_path, hdu, exposure_info):

        array = array_2d_util.numpy_array_2d_from_fits(
            file_path=file_path, hdu=hdu, do_not_scale_image_data=True
        )

        if exposure_info.original_units in "COUNTS":
            return (array * exposure_info.bscale) + exposure_info.bzero
        elif exposure_info.original_units in "CPS":
            return (
                array * exposure_info.exposure_time * exposure_info.bscale
            ) + exposure_info.bzero


class Layout2DACS(lo.Layout2D):
    @classmethod
    def from_ccd(
        cls,
        quadrant_letter,
        parallel_size=2068,
        serial_size=2072,
        serial_prescan_size=24,
        parallel_overscan_size=20,
    ):
        """
        Using an input array of both quadrants in electrons, use the quadrant letter to extract the quadrant from the
        full CCD and perform the rotations required to give correct arctic.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """
        if quadrant_letter == "B" or quadrant_letter == "C":

            return cls.left(
                parallel_size=parallel_size,
                serial_size=serial_size,
                serial_prescan_size=serial_prescan_size,
                parallel_overscan_size=parallel_overscan_size,
            )
        elif quadrant_letter == "A" or quadrant_letter == "D":
            return cls.right(
                parallel_size=parallel_size,
                serial_size=serial_size,
                serial_prescan_size=serial_prescan_size,
                parallel_overscan_size=parallel_overscan_size,
            )
        else:
            raise exc.FrameException(
                "Quadrant letter for FrameACS must be A, B, C or D."
            )

    @classmethod
    def left(
        cls,
        parallel_size=2068,
        serial_size=2072,
        serial_prescan_size=24,
        parallel_overscan_size=20,
    ):
        """
        Use an input array of the left quadrant in electrons and perform the rotations required to give correct
        arctic clocking.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """
        parallel_overscan = reg.Region2D(
            (
                parallel_size - parallel_overscan_size,
                parallel_size,
                serial_prescan_size,
                serial_size,
            )
        )

        serial_prescan = reg.Region2D((0, parallel_size, 0, serial_prescan_size))

        return lo.Layout2D.rotated_from_roe_corner(
            roe_corner=(1, 0),
            shape_native=(parallel_size, serial_size),
            parallel_overscan=parallel_overscan,
            serial_prescan=serial_prescan,
        )

    @classmethod
    def right(
        cls,
        parallel_size=2068,
        serial_size=2072,
        parallel_overscan_size=20,
        serial_prescan_size=51,
    ):
        """
        Use an input array of the right quadrant in electrons and perform the rotations required to give correct
        arctic clocking.

        See the docstring of the `FrameACS` class for a complete description of the Euclid FPA, quadrants and
        rotations.
        """
        parallel_overscan = reg.Region2D(
            (
                parallel_size - parallel_overscan_size,
                parallel_size,
                0,
                serial_size - serial_prescan_size,
            )
        )

        serial_prescan = reg.Region2D(
            (0, parallel_size, serial_size - serial_prescan_size, serial_size)
        )

        return lo.Layout2D.rotated_from_roe_corner(
            roe_corner=(1, 1),
            shape_native=(parallel_size, serial_size),
            parallel_overscan=parallel_overscan,
            serial_prescan=serial_prescan,
        )


class ExposureInfoACS(abstract_array.ExposureInfo):
    def __init__(
        self,
        original_units=None,
        bscale=None,
        bzero=0.0,
        exposure_time=None,
        date_of_observation=None,
        time_of_observation=None,
        hdu=None,
    ):

        super().__init__(
            exposure_time=exposure_time,
            date_of_observation=date_of_observation,
            time_of_observation=time_of_observation,
        )

        self.original_units = original_units
        self.bscale = bscale
        self.bzero = bzero
        self.hdu = hdu

    def array_eps_to_counts(self, array_eps):
        return array_eps_to_counts(
            array_eps=array_eps, bscale=self.bscale, bzero=self.bzero
        )
