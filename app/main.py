import json
from typing import Tuple, Union, List
import uvicorn
from fastapi import FastAPI, status, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from folium import Map, TileLayer
from rio_tiler.io import STACReader # rio_tiler.io.STACReader is a MultiBaseReader
from titiler.core.factory import MultiBaseTilerFactory, TilerFactory
from titiler.mosaic.factory import MosaicTilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.mosaic.errors import MOSAIC_STATUS_CODES

from transform import fetch_external_stac
from algorithms import algorithms

# Define constants
API_URL = "https://earth-search.aws.element84.com/v0"

# Use L2A as it is same as L1C with processing done to remove atmospheric effects
# See: https://forum.step.esa.int/t/clarification-on-difference-between-l1c-and-l2a-data/24940 
COLLECTION = "sentinel-s2-l2a-cogs"  # Sentinel-2, Level 2A, COGs

# Initialize app
app = FastAPI(
    title="Flood Map STAC Tile Server",
    description="A simple STAC tile server for flood map tiles")

# Create tiler factory with custom algorithm
#cog = TilerFactory()
stac = MultiBaseTilerFactory(process_dependency=algorithms.dependency, reader=STACReader)
#mosaic = MosaicTilerFactory(process_dependency=algorithms.dependency)

# Add routers to app
#app.include_router(cog.router, prefix="/cog/", tags=["Cloud Optimized GeoTIFF"])
app.include_router(stac.router, tags=["STAC"])
#app.include_router(mosaic.router, tags=["Mosaic"])

# Add exception handlers
add_exception_handlers(app, DEFAULT_STATUS_CODES)
#add_exception_handlers(app, MOSAIC_STATUS_CODES)

# Add routes
@app.get("/", tags=["Info"])
async def root():
    # Display welcome message and example request
    example_request = "http://127.0.0.1:8000/search/?left=-168.65&bottom=-15.17&right=-168.12&top=-14.45"
    context = {
        "message": "Welcome to the Flood Data API!",
        "example request": example_request,
    }
    return context

@app.get("/search/", response_class=RedirectResponse, tags=["Location Search"])
def get_data(left: float, bottom: float, right: float, top: float) -> RedirectResponse:
    '''
    Retrieve flood data by bounding box (long/lat) coordinates.
    '''
    # Fetch STAC data from Earth Search API
    try:
        #assets = fetch_external_stac(
        item = fetch_external_stac( # for testing
            url=API_URL, 
            collection=COLLECTION, 
            bbox=(left, bottom, right, top))
    except:
        raise HTTPException(status_code=404, detail="Country not found")


    # Redirect to titiler endpoint and return data converted to tiles
    stac_url = item.self_href
    redirect_url = f"/tilejson.json?url={stac_url}&assets=B03&assets=B11"
    redirect_url += "&minzoom=8&maxzoom=14&algorithm=detectFlood"
    redirect_url += "&rescale=-2,2&colormap_name=viridis"
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_302_FOUND,
    )

#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=8000)