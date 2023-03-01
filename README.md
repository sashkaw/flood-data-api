# flood-data-api

### Flood Map STAC Tile Server built with FastAPI and Titiler

- Fetches STAC Sentinel-2 satellite imagery data from Earth Search API
- Calculates Modified Normalized Difference Water Index (MNDWI)
- Applies Otsu thresholding algorithm to identify surface water
- Generates map tiles from classified data using Titiler

# For local development
- Create and activate virtual environment
- Run `pip install -r requirements.txt`
- Run `cd app`
- Run `uvicorn main:app --reload`

# Example API request using Python
```
# your_app.py
import httpx

titiler_endpoint = "http://127.0.0.1:8000"
r = httpx.get(
    url=f"{titiler_endpoint}/search",
    follow_redirects=True,
    params = {
        "left": -168.65,
        "bottom": -15.17,
        "right": -168.12,
        "top": -14.45,
   }
).json()
print(r)
```

# To run tests
- Run `python -m pytest` from app directory