import requests
from typing import Optional, Generator, List, Dict

# NOTE: We cannot use pystac because the service does not implement the QUERY and SORT extensions, so we cannot filter the images.
#       The pystac basic client only provides the basic query parameters: bbox, datetime, limit.
"""
from pystac_client import Client
client = Client.open('https://catalogue.dataspace.copernicus.eu/stac/')
utm_zone = tile[:2]
latitude_band = tile[2:3]
grid_square = tile[3:5]
search = client.search(
    collections=['SENTINEL-2'],
    filter=[f'sentinel:utm_zone = {utm_zone} AND sentinel:latitude_band = {latitude_band} AND sentinel:grid_square = {grid_square}']
)
search.matched()
"""

class Client():
    """
    A class to interact with a SpatioTemporal Asset Client (STAC) endpoint.

    Attributes:
        url (str): The base URL of the STAC Client.
    """
    url: str
    
    def __init__(self, url:str) -> None:
        """
        Initializes the Client with a base URL for the STAC Client.

        Parameters:
            url (str): The base URL of the STAC Client.
        """
        self.url = url.rstrip('/')

    def get_collections(self) -> Optional[List[Dict]]:
        """
        Retrieves a list of all collections available in the STAC Client.

        Returns:
            Optional[List[Dict]]: A list of collection metadata dictionaries if successful, None otherwise.
        """
        response = requests.get(f'{self.url}/collections')
        if response.status_code == 200:
            return response.json().get('collections')
        
    def get_collection_ids(self) -> List[str]:
        """
        Retrieves a list of all collection IDs available in the STAC Client.

        Returns:
            List[str]: A list of collection IDs.
        """
        return [collection['id'] for collection in self.get_collections()]
    
    def get_collection_metadata(self, collectionId:str) -> Optional[Dict]:
        """
        Retrieves metadata for a specific collection by its ID.

        Parameters:
            collectionId (str): The ID of the collection.

        Returns:
            Optional[Dict]: A dictionary containing the collection's metadata if successful, None otherwise.
        """
        if any([collection['id'] == collectionId for collection in self.get_collections()]):
            response = requests.get(f'{self.url}/collections/{collectionId}')
            if response.status_code == 200:
                return response.json()
        return None
            
    def get_queryables(self, collectionId:str) -> Optional[List[str]]:
        """
        Retrieves the list of queryable properties for a specific collection.

        Parameters:
            collectionId (str): The ID of the collection.

        Returns:
            Optional[List[str]]: A list of queryable property keys if successful, None otherwise.
        """
        response = requests.get(f'{self.url}/collections/{collectionId}/queryables')
        if response.status_code == 200:
            return response.json().get('properties').keys()
        return None

    def get_files(self,
        collectionId:str,
        spatial_extent:Optional[dict]=None,
        temporal_extent:Optional[list]=None,
        max_cloud_cover:Optional[int]=100,
        properties: Optional[dict]={},
        limit:Optional[int]=100,
        latest: Optional[bool]=False
    ) -> Generator[Dict, None, None]:
        """
        Retrieves files (items) from a specific collection that match given criteria.

        Parameters:
            collectionId (str): The ID of the collection.
            spatial_extent (Optional[dict]): The spatial extent (bounding box) to filter results.
            temporal_extent (Optional[list]): The temporal extent (time range) to filter results.
            max_cloud_cover (Optional[int]): Maximum cloud cover percentage allowed for results (default is 100).
            properties (Optional[dict]): Additional properties to filter results.
            limit (Optional[int]): The maximum number of items to return per request (default is 100).
            latest (Optional[bool]): Whether to return only the latest items (default is False).

        Yields:
            Dict: A generator yielding items (files) matching the criteria.
        """
        # https://openeo.org/documentation/0.4/developers/api/reference.html#tag/EO-Data-Discovery/paths/~1collections/get
        url = f'{self.url}/collections/{collectionId}/items?'
        url_parameters = []
        if spatial_extent:
            url_parameters.append(f'bbox={spatial_extent[0]},{spatial_extent[1]},{spatial_extent[2]},{spatial_extent[3]}')
        if temporal_extent:
            start_datetime = temporal_extent[0]
            end_datetime = temporal_extent[1]
            url_parameters.append(f'datetime={start_datetime}/{end_datetime}')
        url_parameters.append(f'limit={limit}')
        url_parameters.append('sortby=-datetime') # LATEST FIRST
        url = url + '&'.join(url_parameters)
        try:
            yield from self.request_pages(url=url, max_cloud_cover=max_cloud_cover, properties=properties, latest=latest)
        except requests.exceptions.ConnectionError:
            try:
                yield from self.request_pages(url=url, max_cloud_cover=max_cloud_cover, properties=properties, latest=latest)
            except requests.exceptions.ConnectionError:
                raise
    
    def request_pages(self, url:str, max_cloud_cover:int, properties:dict, latest:bool, start_datetime:Optional[str]=None) -> Generator[Dict, None, None]:
        """
        Requests pages of items from the STAC API and filters them based on cloud cover, properties, and temporal criteria.

        Parameters:
            url (str): The URL to request items from.
            max_cloud_cover (int): Maximum cloud cover percentage allowed for results.
            properties (dict): Additional properties to filter results.
            latest (bool): Whether to return only the latest items.
            start_datetime (Optional[str]): The start datetime to filter results if 'latest' is True.

        Yields:
            Dict: A generator yielding items (files) matching the criteria.
        """
        response = requests.get(url, timeout=120)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features')
            if features:
                yielded = 0
                features =[feature for feature in features if all((key, value) in feature['properties'].items() for key, value in properties.items())]
                if max_cloud_cover and max_cloud_cover != 100:
                    features = [feature for feature in features if 'cloudCover' in feature['properties'].keys() and feature['properties']['cloudCover'] < max_cloud_cover]
                if features and latest and not start_datetime:
                    start_datetime = features[0]['properties']['start_datetime'][:10]
                for feature in features:
                    if not latest or (latest and feature['properties']['start_datetime'][:10] == start_datetime):
                        yielded += 1
                        yield feature
                next_page = [link['href'] for link in data['links'] if link['rel'] == 'next']
                next_page = next_page[0] if next_page else None
                if next_page:
                    yield from self.request_pages(url=next_page, max_cloud_cover=max_cloud_cover, properties=properties, latest=latest, start_datetime=start_datetime)