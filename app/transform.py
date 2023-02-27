import pystac
from pystac_client import Client
from shapely.geometry import Point
import rioxarray
from pyproj import CRS
import geopandas as gpd
from folium import Map, TileLayer
import numpy as np
import xarray
#import matplotlib.pyplot as plt
#from matplotlib.colors import ListedColormap
import dask
import rasterio
from rasterio.plot import show
import json
from datetime import datetime
import pandas as pd
import httpx
from typing import Union
from shapely.geometry import Polygon, mapping
import pycountry
from threading import Lock
import os

# Helper functions
# TODO - add class for interacting with stac data, and class for processing raster data?

def get_country_bbox(country: str, bounds: dict) -> dict[float]:
    '''
    Desc: Get bounding box coordinates by name of country

    Example usage: country_bbox = get_country_bbox("american SamOA", dict_of_countries)
    '''
    # Search for country by name
    common_name_data = pycountry.countries.get(common_name=country)
    name_data = pycountry.countries.get(name=country)

    # Check that country name search returned valid item                                    
    if(not common_name_data and not name_data):
        raise AttributeError("Invalid country name")
    elif(None in [common_name_data, name_data]):
        country_data = common_name_data or name_data
    else:
        country_data = common_name_data

    # Get country code
    country_code = country_data.alpha_2.lower()
    # Extract bounding box
    bbox = bounds.get(country_code).get("boundingBox")
    left = bbox.get("sw").get("lon")
    bottom = bbox.get("sw").get("lat")
    right = bbox.get("ne").get("lon")
    top = bbox.get("ne").get("lat")

    return [left, bottom, right, top]


def get_time_params() -> list[str]:
    '''
    Desc: Get start and end dates for external API query
    Example usage: start, end = get_time_params()
    '''
    # Get current date, and date within date offset for querying satellite data
    current_time = datetime.now()
    date_end = current_time.strftime("%Y-%m-%d")
    date_offset = pd.Timedelta(days=1) # Set days to 1 to avoid duplicates (for now?)
    date_start = (current_time - date_offset).strftime("%Y-%m-%d")

    return [date_start, date_end]
    

def fetch_external_stac(url: str, collection: str, country: str, country_list: dict) -> dict[pystac.asset.Asset]:
    '''
    Desc: Fetch stac data from external api
    Example: stac = fetch_external_stac("https://www.your_api.com", "collection_name")
    '''
    # Initialize client
    print("Fetching assets...")
    client = Client.open(url)

    # Get parameters for fetching external STAC data 
    country_bbox = get_country_bbox(country=country, bounds=country_list)
    start, end = get_time_params()

    # Run search
    search = client.search(
        collections=[collection],
        bbox=country_bbox,
        max_items=500,
        datetime= f"{start}/{end}",
        query={
        "eo:cloud_cover":{"lt":10}, 
        "sentinel:valid_cloud_cover": {"eq": True}
        }, # Select items with lower cloud cover
    )

    # Get items from query
    items = search.get_all_items()
    #search.matched()
    #assets = items[0].assets # TODO - expand this to mosaic data from multiple tiles
    #return assets
    return items[0] # for testing


def match_projections(assets: dict[pystac.asset.Asset]) -> dict[xarray.core.dataarray.DataArray]:
    '''
    Desc: Match projections for two raster bands as needed.
    Example: bands = match_projections(test_assets)
    '''
    # Extract bands of interest with the use of Dask chunked arrays
    green_band = rioxarray.open_rasterio(assets["B03"].href, lock=False, chunks = "auto")
    swir_band = rioxarray.open_rasterio(assets["B12"].href, lock=False, chunks = "auto")
    
    # Reproject data to match shapes if unequal
    if(green_band.shape != swir_band.shape):
        print("Reprojecting...")

        if(green_band.shape > swir_band.shape):
            # Use tiled=True to write as chunked GeoTIFF,
            # use Lock() to synchronize threads
            # use compute=False for lazy execution
            green_band = green_band.rio.reproject_match(swir_band, tiled=True, lock=Lock(), compute=False)

        else:
            swir_band = swir_band.rio.reproject_match(green_band, tiled=True, lock=Lock(), compute=False)

    return {"green_band": green_band, "swir_band": swir_band}


def calc_mndwi(bands: dict[xarray.core.dataarray.DataArray]) -> xarray.core.dataarray.DataArray:
    '''
    Desc: Calculate Modified Normalized Difference Water Index (MNDWI) for detecting water
    Example: mndwi = calc_mndwi(bands)
    '''
    green_band = bands.get("green_band")
    swir_band = bands.get("swir_band")

    # Calculate the Modified Normalized Difference Water Index (MNDWI) for detecting water
    print("Calculating MNDWI...")
    mndwi = (green_band - swir_band) / (green_band + swir_band)
    return mndwi


def classify_raster(class_bins: Union[list[float], tuple[float]], raster) -> xarray.core.dataarray.DataArray:
    '''
    Desc: Classify raster and save as GeoTIFF
    Example: classified, filename, filepath = classify_raster((0.0, 0.6), your_raster)
    '''

    # Classify data with provided bins
    classified = xarray.apply_ufunc(
        np.digitize,
        raster,
        class_bins,
        dask="allowed")
    
    # Write to disk
    filename = "mndwi_" + datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    filepath = "./data/" + filename + ".tif"
    classified.rio.to_raster(filepath)

    return classified, filename, filepath


def transform_raster(assets: dict[pystac.asset.Asset]) -> dict[xarray.core.dataarray.DataArray, str, str]:
    '''
    Process raster bands, calculate MNDWI, and classify the data.
    '''
    bands = match_projections(assets)
    mndwi = calc_mndwi(bands)
    classified, filename, filepath = classify_raster((0.0, 15.0), mndwi)
    return {"classified": classified, "filename": filename, "filepath": filepath}


def create_stac_catalog() -> pystac.Catalog:
    '''
    Create new STAC catalog
    '''
    if(os.path.exists("stac")):
        print("exists")
        catalog = pystac.read_file("./stac/catalog.json")
        return catalog
    else:
        catalog = pystac.Catalog(id='flood-data-catalog', description='Flood data catalog.')
        return catalog


def get_bbox_and_footprint(raster: xarray.core.dataarray.DataArray) -> tuple[list, mapping]:
    ''' 
    Desc: Extract bounding box coordinates from raster.clear
    Example: bbox, footprint = get_bbox_and_footprint(your_raster)
    '''
    bounds = raster.rio.bounds()
    bbox = [bounds[0], bounds[1], bounds[2], bounds[3]]
    footprint = Polygon([
        [bounds[0], bounds[1]],
        [bounds[0], bounds[3]],
        [bounds[2], bounds[3]],
        [bounds[2], bounds[1]]
    ])

    return (bbox, mapping(footprint))


def add_stac_item(
        raster: xarray.core.dataarray.DataArray,
        catalog: pystac.Catalog, 
        filename: str, 
        filepath: str) -> None:
    '''
    Desc: Create STAC item and add to STAC catalog
    '''

    # Get bbox and footprint for stac fields
    bbox, footprint = get_bbox_and_footprint(raster)
    
    # Create STAC item
    item = pystac.Item(id=filename,
                 geometry=footprint,
                 bbox=bbox,
                 datetime=datetime.utcnow(),
                 properties={})

    # Add item to catalog
    catalog.add_item(item)

    # Add link to imagery
    # TODO: Connect to DB
    item.add_asset(
    key='image',
    asset=pystac.Asset(
        href=filepath, # TODO: get as in memory object?
        media_type=pystac.MediaType.GEOTIFF
        )
    )
    #  Create normalized set of HREFs for each STAC object in the catalog
    catalog.normalize_hrefs('./stac')

    # Save catalog
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
