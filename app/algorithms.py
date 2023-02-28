import numpy as np
from titiler.core.algorithm import BaseAlgorithm
from titiler.core.algorithm import algorithms as default_algorithms
from rio_tiler.models import ImageData
from pygeotile.point import Point
import xarray
from skimage.filters import threshold_otsu

class DetectFlood(BaseAlgorithm):
    
    # Metadata
    input_nbands: int = 2
    output_nbands: int = 1

    # Bins
    class_bins = (0,15)
 
    def __call__(self, img: ImageData, *args, **kwargs):
        #print("img.data.shape: ", img.data.shape)
        #for arg in args:
        #    print("Arg:", arg)
        # Extract bands of interest
        green_band = img.data[0].astype("float32")
        swir_band = img.data[1].astype("float32")
        
        # Calculate Modified Normalized Water Difference Index
        # Note: Use 0 to fill nodata areas with 0
        print(green_band.min(), green_band.max(), swir_band.min(), swir_band.max())
        
        #ndwi_arr = np.where(img.mask, (green_band - swir_band) / (green_band + swir_band), 0)
        #mndwi_arr = (green_band - swir_band) / (green_band + swir_band)
        numerator = (green_band - swir_band)
        denominator = (green_band + swir_band)
        # Use np.divide to avoid divide by zero errors
        mndwi_arr = np.divide(numerator, denominator, np.zeros_like(numerator), where=denominator!=0)

        # Classify output
        #classified_arr = xarray.apply_ufunc(
        #    np.digitize,
        #    mndwi_arr,
        #    self.class_bins,
        #    dask="allowed")

        # Apply Otsu Thresholding method
        otsu_threshold = threshold_otsu(mndwi_arr)
        print("otsu:", otsu_threshold)

        # Use threshold to classify data
        classified_arr = mndwi_arr >= otsu_threshold
        #classified_arr = np.where(mndwi_arr >= otsu_threshold, mndwi_arr, 0)
        #print(classified_arr.min(), classified_arr.max())
        print(np.unique(classified_arr))
        #print(np.quantile(classified_arr, q=(0,0.25,0.5,0.75,1)))

        #mndwi_arr *= (255.0/mndwi_arr.max())

        #classified_arr = np.digitize(x=mndwi_arr, bins=self.class_bins)
       
        # ImageData only accepts image in form of (count, height, width)
        classified_arr = np.around(classified_arr).astype(int)
        #classified_arr = np.expand_dims(classified_arr, axis=0).astype(self.output_dtype)
        classified_arr = np.expand_dims(classified_arr, axis=0)
        
        #print(classified_arr.min(), classified_arr.max())
        #print(classified_arr)

        return ImageData(
            classified_arr,
            #np.expand_dims(mndwi_arr, axis=0).astype(int),
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


