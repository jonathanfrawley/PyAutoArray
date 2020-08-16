import logging
import numpy as np
import copy

import autoarray as aa

from autoarray import exc
from autoarray.dataset import abstract_dataset, preprocess
from autoarray.structures import arrays, grids, visibilities as vis, kernel
from autoarray.operators import transformer as trans


logger = logging.getLogger(__name__)


class AbstractInterferometer(abstract_dataset.AbstractDataset):
    def __init__(
        self, visibilities, noise_map, uv_wavelengths, positions=None, name=None
    ):

        super().__init__(
            data=visibilities, noise_map=noise_map, positions=positions, name=name
        )

        self.uv_wavelengths = uv_wavelengths

    @property
    def visibilities(self):
        return self.data

    @property
    def amplitudes(self):
        return self.visibilities.amplitudes

    @property
    def phases(self):
        return self.visibilities.phases

    @property
    def uv_distances(self):
        return np.sqrt(
            np.square(self.uv_wavelengths[:, 0]) + np.square(self.uv_wavelengths[:, 1])
        )

    def modified_visibilities_from_visibilities(self, visibilities):

        interferometer = copy.deepcopy(self)
        interferometer.data = visibilities
        return interferometer


class AbstractMaskedInterferometerSettings(
    abstract_dataset.AbstractMaskedDatasetSettings
):
    def __init__(
        self,
        grid_class=grids.Grid,
        grid_inversion_class=grids.Grid,
        fractional_accuracy=0.9999,
        sub_steps=None,
        pixel_scales_interp=None,
        transformer_class=trans.TransformerNUFFT,
    ):
        """
          The lens dataset is the collection of data_type (image, noise-map), a mask, grid, convolver \
          and other utilities that are used for modeling and fitting an image of a strong lens.

          Whilst the image, noise-map, etc. are loaded in 2D, the lens dataset creates reduced 1D arrays of each \
          for lens calculations.

          Parameters
          ----------
          imaging: im.Imaging
              The imaging data_type all in 2D (the image, noise-map, etc.)
          real_space_mask: msk.Mask
              The 2D mask that is applied to the image.
          sub_size : int
              The size of the sub-grid used for each lens SubGrid. E.g. a value of 2 grid each image-pixel on a 2x2 \
              sub-grid.
          positions : [[]]
              Lists of image-pixel coordinates (arc-seconds) that mappers close to one another in the source-plane(s), \
              used to speed up the non-linear sampling.
          pixel_scales_interp : float
              If *True*, expensive to compute mass profile deflection angles will be computed on a sparse grid and \
              interpolated to the grid, sub and blurring grids.
          inversion_pixel_limit : int or None
              The maximum number of pixels that can be used by an inversion, with the limit placed primarily to speed \
              up run.
          """

        super().__init__(
            grid_class=grid_class,
            grid_inversion_class=grid_inversion_class,
            fractional_accuracy=fractional_accuracy,
            sub_steps=sub_steps,
            pixel_scales_interp=pixel_scales_interp,
        )

        self.transformer_class = transformer_class


class AbstractMaskedInterferometer(abstract_dataset.AbstractMaskedDataset):
    def __init__(
        self,
        interferometer,
        visibilities_mask,
        real_space_mask,
        settings=AbstractMaskedInterferometerSettings(),
    ):
        """
        The lens dataset is the collection of data_type (image, noise-map), a mask, grid, convolver \
        and other utilities that are used for modeling and fitting an image of a strong lens.

        Whilst the image, noise-map, etc. are loaded in 2D, the lens dataset creates reduced 1D arrays of each \
        for lens calculations.

        Parameters
        ----------
        imaging: im.Imaging
            The imaging data_type all in 2D (the image, noise-map, etc.)
        real_space_mask: msk.Mask
            The 2D mask that is applied to the image.
        """

        super().__init__(
            dataset=interferometer, mask=real_space_mask, settings=settings
        )

        self.transformer = self.settings.transformer_class(
            uv_wavelengths=interferometer.uv_wavelengths,
            real_space_mask=real_space_mask,
        )

        self.visibilities = interferometer.visibilities
        self.noise_map = interferometer.noise_map
        self.visibilities_mask = visibilities_mask

    @property
    def interferometer(self):
        return self.dataset

    @property
    def data(self):
        return self.visibilities

    @property
    def uv_distances(self):
        return self.interferometer.uv_distances

    @property
    def real_space_mask(self):
        return self.mask

    def signal_to_noise_map(self):
        return self.visibilities / self.noise_map

    def modify_noise_map(self, noise_map):

        masked_interferometer = copy.deepcopy(self)

        masked_interferometer.noise_map = noise_map

        return masked_interferometer


class AbstractSimulatorInterferometer:
    def __init__(
        self,
        uv_wavelengths,
        exposure_time_map,
        background_sky_map=None,
        transformer_class=trans.TransformerDFT,
        noise_sigma=0.1,
        noise_if_add_noise_false=0.1,
        noise_seed=-1,
    ):
        """A class representing a Imaging observation, using the shape of the image, the pixel scale,
        psf, exposure time, etc.

        Parameters
        ----------
        real_space_shape_2d : (int, int)
            The shape of the observation. Note that we do not simulator a full Imaging frame (e.g. 2000 x 2000 pixels for \
            Hubble imaging), but instead just a cut-out around the strong lens.
        real_space_pixel_scales : float
            The size of each pixel in arc seconds.
        psf : PSF
            An arrays describing the PSF kernel of the image.
        exposure_time_map : float
            The exposure time of an observation using this data_type.
        background_sky_map : float
            The level of the background sky of an observationg using this data_type.
        """

        self.uv_wavelengths = uv_wavelengths
        self.exposure_time_map = exposure_time_map
        self.background_sky_map = background_sky_map
        self.transformer_class = transformer_class
        self.noise_sigma = noise_sigma
        self.noise_if_add_noise_false = noise_if_add_noise_false
        self.noise_seed = noise_seed

    def from_image(self, image, name=None):
        """
        Create a realistic simulated image by applying effects to a plain simulated image.

        Parameters
        ----------
        name
        real_space_image : ndarray
            The image before simulating (e.g. the lens and source galaxies before optics blurring and UVPlane read-out).
        real_space_pixel_scales: float
            The scale of each pixel in arc seconds
        exposure_time_map : ndarray
            An array representing the effective exposure time of each pixel.
        psf: PSF
            An array describing the PSF the simulated image is blurred with.
        background_sky_map : ndarray
            The value of background sky in every image pixel (electrons per second).
        add_noise: Bool
            If True poisson noise_maps is simulated and added to the image, based on the total counts in each image
            pixel
        noise_seed: int
            A seed for random noise_maps generation
        """

        transformer = self.transformer_class(
            uv_wavelengths=self.uv_wavelengths, real_space_mask=image.mask
        )

        if self.background_sky_map is not None:
            background_sky_map = self.background_sky_map
        else:
            background_sky_map = arrays.Array.zeros(
                shape_2d=image.shape_2d, pixel_scales=image.pixel_scales
            )

        image = image + background_sky_map

        visibilities = transformer.visibilities_from_image(image=image)

        if self.noise_sigma is not None:
            visibilities = preprocess.data_with_gaussian_noise_added(
                data=visibilities, sigma=self.noise_sigma, seed=self.noise_seed
            )
            noise_map = vis.Visibilities.full(
                fill_value=self.noise_sigma, shape_1d=(visibilities.shape[0],)
            )
        else:
            noise_map = vis.Visibilities.full(
                fill_value=self.noise_if_add_noise_false,
                shape_1d=(visibilities.shape[0],),
            )

        if np.isnan(noise_map).any():
            raise exc.DataException(
                "The noise-map has NaN values in it. This suggests your exposure time and / or"
                "background sky levels are too low, creating signal counts at or close to 0.0."
            )

        return Interferometer(
            visibilities=visibilities,
            noise_map=noise_map,
            uv_wavelengths=transformer.uv_wavelengths,
            name=name,
        )


class Interferometer(AbstractInterferometer):
    @classmethod
    def from_fits(
        cls,
        visibilities_path,
        noise_map_path,
        uv_wavelengths_path,
        visibilities_hdu=0,
        noise_map_hdu=0,
        uv_wavelengths_hdu=0,
        positions_path=None,
    ):
        """Factory for loading the interferometer data_type from .fits files, as well as computing properties like the noise-map,
        exposure-time map, etc. from the interferometer-data_type.

        This factory also includes a number of routines for converting the interferometer-data_type from unit_label not supported by PyAutoLens \
        (e.g. adus, electrons) to electrons per second.

        Parameters
        ----------
        """

        visibilities = aa.Visibilities.from_fits(
            file_path=visibilities_path, hdu=visibilities_hdu
        )

        noise_map = aa.VisibilitiesNoiseMap.from_fits(
            file_path=noise_map_path, hdu=noise_map_hdu
        )

        uv_wavelengths = aa.util.array.numpy_array_2d_from_fits(
            file_path=uv_wavelengths_path, hdu=uv_wavelengths_hdu
        )

        if positions_path is not None:

            positions = grids.GridCoordinates.from_file(file_path=positions_path)

        else:

            positions = None

        return Interferometer(
            visibilities=visibilities,
            noise_map=noise_map,
            uv_wavelengths=uv_wavelengths,
            positions=positions,
        )

    def output_to_fits(
        self,
        visibilities_path=None,
        noise_map_path=None,
        uv_wavelengths_path=None,
        overwrite=False,
    ):

        if visibilities_path is not None:
            self.visibilities.output_to_fits(
                file_path=visibilities_path, overwrite=overwrite
            )

        if self.noise_map is not None and noise_map_path is not None:
            self.noise_map.output_to_fits(file_path=noise_map_path, overwrite=overwrite)

        if self.uv_wavelengths is not None and uv_wavelengths_path is not None:
            aa.util.array.numpy_array_2d_to_fits(
                array_2d=self.uv_wavelengths,
                file_path=uv_wavelengths_path,
                overwrite=overwrite,
            )


class MaskedInterferometerSettings(AbstractMaskedInterferometerSettings):

    pass


class MaskedInterferometer(AbstractMaskedInterferometer):

    pass


class SimulatorInterferometer(AbstractSimulatorInterferometer):

    pass
