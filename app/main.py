import json
from typing import Tuple
import uvicorn
from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from folium import Map, TileLayer
from rio_tiler.io import STACReader # rio_tiler.io.STACReader is a MultiBaseReader
from titiler.core.factory import MultiBaseTilerFactory, TilerFactory
from titiler.mosaic.factory import MosaicTilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.mosaic.errors import MOSAIC_STATUS_CODES

from transform import create_stac_catalog, fetch_external_stac, transform_raster, add_stac_item
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
app = FastAPI(
    title="Flood Map STAC Tile Server", 
    description="A STAC tile server to serve dynamic flood data")

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
add_exception_handlers(app, MOSAIC_STATUS_CODES)

# Create stac catalog
#catalog = create_stac_catalog()

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
        url=f"/tilejson.json?url={stac_url}&assets=B03&assets=B11&minzoom=8&maxzoom=14&algorithm=detectFlood&rescale=-1,1&colormap_name=viridis",
        status_code=status.HTTP_302_FOUND,
    )
    return stac_url

#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=8000)