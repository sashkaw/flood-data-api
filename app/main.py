import json
from typing import Tuple
from fastapi import FastAPI, status, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from folium import Map, TileLayer
from rio_tiler.io import STACReader # rio_tiler.io.STACReader is a MultiBaseReader
from titiler.core.factory import MultiBaseTilerFactory

from transform import *
from algorithms import algorithms


# Define constants
API_URL = "https://earth-search.aws.element84.com/v0"

# Use L2A as it is same as L1C with processing done to remove atmospheric effects
# See: https://forum.step.esa.int/t/clarification-on-difference-between-l1c-and-l2a-data/24940 
COLLECTION = "sentinel-s2-l2a-cogs"  # Sentinel-2, Level 2A, COGs

# Get country bounding box
with open("./countries.json", "r") as f:
    country_bounds = json.load(f)

# Initialize app
app = FastAPI(title="Flood Map STAC Tile Server", description="A lightweight STAC tile server")
# Create tiler factory with custom algorithm
cog = MultiBaseTilerFactory(reader=STACReader, process_dependency=algorithms.dependency)
app.include_router(cog.router, tags=["STAC"])

# Create stac catalog
catalog = create_stac_catalog()

# Add routes
@app.get("/", tags=["Home"])
async def root():
    return {"message": "Welcome to the Flood Data API!"}

@app.get("/search/", response_class=RedirectResponse, tags=["Location Search"])
def get_data(country: str):
    '''
    Retrieve flood data by country.
    '''
    # Fetch STAC data from Earth Search API
    try:
        #assets = fetch_external_stac(
        item = fetch_external_stac( # for testing
            url=API_URL, 
            collection=COLLECTION, 
            country=country,
            country_list=country_bounds)
    except:
        raise HTTPException(status_code=404, detail="Country not found")

    # Process STAC data
    #transformed_dict = transform_raster(assets=assets)
    #classified = transformed_dict.get("classified")
    #print(classified.rio.bounds())

    # Save item in STAC catalog
    #filename = transformed_dict.get("filename")
    #add_stac_item(
    #    raster=classified, 
    #    catalog=catalog, 
    #    filename=filename,
    #    filepath=transformed_dict.get("filepath"))

    # Redirect to titiler endpoint and return data converted to tiles
    #stac_url = f"./stac/{filename}/{filename}.json"
    #print(stac_url)
    stac_url = item.self_href
    return RedirectResponse(
        url=f"/tilejson.json?url={stac_url}&assets=green&assets=swir16&minzoom=8&maxzoom=14&algorithm=MNDWI",
        #url=f"/tilejson.json?url={stac_url}&assets=image&minzoom=8&maxzoom=14&algorithm=hillshade&buffer=3",
        #url=f"/tilejson.json?url={stac_url}&assets=image&minzoom=8&maxzoom=14&expression=(green-swir)/(green+swir)",
        status_code=status.HTTP_302_FOUND,
    )