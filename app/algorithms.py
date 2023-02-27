import numpy as np
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as default_algorithms
from rio_tiler.models import ImageData
from pygeotile.point import Point
import xarray

class MNDWI(BaseAlgorithm):
    
    # Metadata
    input_nbands: int = 2
    output_nbands: int = 1

    # Bins
    class_bins = (0,15)
 
    def __call__(self, img: ImageData):
        # Extract bands of interest
        green_band = img.data[0].astype("float32")
        swir_band = img.data[1].astype("float32")
        
        # Calculate Modified Normalized Water Difference Index
        # Note: Use 0 to fill nodata areas with 0
        mndwi_arr = np.where(img.mask, (green_band - swir_band) / (green_band + swir_band), 0)

        # Classify output
        #classified_arr = xarray.apply_ufunc(
        #    np.digitize,
        #    mndwi_arr,
        #    self.class_bins,
        #    dask="allowed")

        #classified_arr = np.digitize(x=mndwi_arr, bins=self.class_bins)
       
        # ImageData only accept image in form of (count, height, width)
        classified_arr = np.expand_dims(mndwi_arr, axis=0).astype(self.output_dtype)

        return ImageData(
            classified_arr,
            img.mask,
            assets=img.assets,
            crs=img.crs,
            bounds=img.bounds,
        )
    
# Register algorithm
algorithms = default_algorithms.register(
    {
    "MNDWI": MNDWI,
    }
)


