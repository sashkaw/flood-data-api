# flood-data-api

### Flood Map STAC Tile Server built with FastAPI and Titiler

- Fetches STAC Sentinel-2 satellite imagery data from Earth Search API
- Transforms raster data to identify regions with water using rioxarray and Dask
- Generates map tiles from classified data using Titiler

# For local development
- Create and activate virtual environment
- Run `pip install -r requirements.txt`
- Run `cd app`
- Run `uvicorn main:app --reload`

# To run tests
- Run `python -m pytest` from app directory
