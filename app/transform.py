import pystac
from pystac_client import Client
from datetime import datetime
import pandas as pd
from typing import Union, Tuple, List, Dict

# Helper functions

def get_time_params() -> List[str]:
    '''
    Desc: Get start and end dates for external API query
    Example usage: start, end = get_time_params()
    '''
    # Get current date, and date within date offset for querying satellite data
    current_time = datetime.now()
    date_end = current_time.strftime("%Y-%m-%d")
    date_offset = pd.Timedelta(days=2)
    date_start = (current_time - date_offset).strftime("%Y-%m-%d")

    return [date_start, date_end]
    

def fetch_external_stac(url: str, collection: str, bbox: Union[Tuple[float], List[float]]) -> Dict[str, pystac.asset.Asset]:
    '''
    Desc: Fetch stac data from external api
    Example: stac = fetch_external_stac(
                        url="https://www.your_api.com", 
                        collection="collection_name", 
                        bbox=(-168.65178856189547, -15.1700621933571, -168.117486492895, -14.454757819240648))
    '''
    # Initialize client
    print("Fetching assets...")
    client = Client.open(url)

    # Get parameters for fetching external STAC data
    start, end = get_time_params()

    # Run search
    search = client.search(
        collections=[collection],
        bbox=bbox,
        max_items=500,
        datetime= f"{start}/{end}",
        query={
        "eo:cloud_cover":{"lt":20}, 
        "sentinel:valid_cloud_cover": {"eq": True}
        }, # Select items with lower cloud cover
    )

    # Get items from query
    items = search.get_all_items()
    #search.matched()
    #assets = items[0].assets # TODO - expand this to mosaic / merge data from multiple rasters
    return items[0]