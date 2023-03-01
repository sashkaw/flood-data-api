import numpy as np
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as default_algorithms
from rio_tiler.models import ImageData
from pygeotile.point import Point
import xarray
from skimage.filters import threshold_otsu

class DetectFlood(BaseAlgorithm):
    '''
    Desc: Algorithm to calculate Modified Normalized Difference Water Index (MNDWI), 
    and apply Otsu thresholding algorithm to identify surface water.
    '''
    
    # Metadata
    input_nbands: int = 2
    output_nbands: int = 1
 
    def __call__(self, img: ImageData, *args, **kwargs):
        # Extract bands of interest
        green_band = img.data[0].astype("float32")
        swir_band = img.data[1].astype("float32")
        
        # Calculate Modified Normalized Difference Water Index (MNDWI) 
        numerator = (green_band - swir_band)
        denominator = (green_band + swir_band)
        # Use np.divide to avoid divide by zero errors
        mndwi_arr = np.divide(numerator, denominator, np.zeros_like(numerator), where=denominator!=0)

        # Apply Otsu thresholding method
        otsu_threshold = threshold_otsu(mndwi_arr)

        # Use Otsu threshold to classify the computed MNDWI
        classified_arr = mndwi_arr >= otsu_threshold
       
        # Reshape data -> ImageData only accepts image in form of (count, height, width)
        #classified_arr = np.around(classified_arr).astype(int)
        #classified_arr = np.expand_dims(classified_arr, axis=0).astype(self.output_dtype)
        classified_arr = np.expand_dims(classified_arr, axis=0).astype(int)

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
    "detectFlood": DetectFlood,
    }
)


