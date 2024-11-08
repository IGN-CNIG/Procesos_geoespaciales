import json
import logging
import os
import time
from typing import List, Dict, Any, Optional

import openeo
import openeo.rest

from src.STAC import Client
from src.AWS import AWSService
from src.constants import S2_Bands
from src.utils import get_area, get_geometry_envelope, apply_contrast_enhancement

TILE_WIDTH = TILE_HEIGHT = 109.8 * 1000 # METERS


class SentinelTile():
    """
    Class for handling Sentinel satellite tile processing, including querying a catalog, 
    downloading datacubes, and applying contrast enhancements to satellite images.
    """
    logger:logging.Logger = logging.getLogger(__name__)  # Obtain a logger for this module/class
    tile_id = None
    
    def __init__(self, region_name:str, tile_id: str, catalog_url:Optional[str] = 'https://catalogue.dataspace.copernicus.eu/stac/', openeo_url:Optional[str] = 'https://openeo.dataspace.copernicus.eu', datacubes_dir:Optional[str] = 'DATACUBES', service_dir:Optional[str] = 'OUTPUT') -> None:
        """
        Initialize the SentinelTile instance with STAC and OpenEO clients and a tile ID.

        Parameters:
            catalog_url (str): The URL of the STAC catalog.
            openeo_url (str): The URL of the OpenEO service.
            tile_id (str): The identifier for the satellite tile to be processed.
            datacubes_dir (Optional[str]): Directory for saving datacubes. Default is 'DATACUBES'.
            service_dir (Optional[str]): Directory for output files. Default is 'OUTPUT'.

        Example:
            >>> tile = SentinelTile('T29TNJ')
        """
        self.stac_client = Client(url=catalog_url)
        self.openeo_client = openeo.connect(url=openeo_url)
        self.tile_id = tile_id
        self.region = region_name
        self.log(f'[{self.tile_id}] Start processing tile.')
        
        # Allow dependency injection for directories or fallback to environment variables
        self.datacubes_dir = os.getenv('DATACUBES_DIR') or datacubes_dir
        os.makedirs(self.datacubes_dir, exist_ok=True)
        
        self.service_dir = os.getenv('SERVICE_DIR') or service_dir
        os.makedirs(self.service_dir, exist_ok=True)
        
    @classmethod
    def log(cls, message:str, level:Optional[str] = logging.INFO) -> None:
        """
        Logs a message at the specified logging level if the logger is active, otherwise self.logs it in console.

        Parameters:
            message (str): The message to log.
            level (Optional[int]): The logging level to use (e.g., logging.DEBUG, logging.INFO).

        If the level is not recognized, the message will be logged at the INFO level.
        """
        if cls.logger:
            if level == logging.DEBUG:
                cls.logger.debug(message)
            elif level == logging.WARNING:
                cls.logger.warning(message)
            elif level == logging.ERROR:
                cls.logger.error(message)
            elif level == logging.CRITICAL:
                cls.logger.critical(message)
            else:
                cls.logger.info(message)
        else:
            print(message)
        
        
    def get_bbox(self) -> List[float]:
        """
        Get the bounding box coordinates for the tile ID from the military grid.

        Returns:
            List[float]: A list representing the bounding box as [west, east, south, north].
                        Returns an empty list if the tile is not found.

        Example:
            >>> tile.get_bbox()
            [-9.55, 40.05, -9.20, 40.30]
        """
        envelope = get_geometry_envelope(self.tile_id)
        if envelope is not None:
            return [envelope[0], envelope[2], envelope[1], envelope[3]]
        
        return []
    
    def query_catalog(self, date_range: List[str], max_cloud_cover: Optional[int] = 100, level: Optional[str] = '2A') -> List[Dict[str, Any]]:
        """
        Query the STAC catalog for satellite imagery based on the provided parameters.

        Parameters:
            date_range (List[str]): The date range that must be fetched from the catalog.
            max_cloud_cover (int): The maximum allowed cloud cover percentage (0-100).
            level (Optional[str]): The product level to query (e.g., '2A', '1C'). Default is '2A'.

        Returns:
            List[Dict[str, Any]]: A list of image metadata dictionaries returned by the catalog query.

        Example:
            >>> tile.query_catalog(days_offset=30, max_cloud_cover=10)
            [{'id': 'S2A_MSIL2A_20240901T123456_N0511_R080_T29TNJ_20240901T130456', ...}]
        """
        # satellite can be S1 or S2
        # Access to the STAC Client, we cannot use pystac because the service does not implement QUERY and SORT among other optional implementations we need.
        # https://documentation.dataspace.copernicus.eu/APIs/STAC.html#items-search-in-a-stac-collection
        # Determine product type based on satellite and input parameters
        self.log(f'[{self.tile_id}] Querying STAC Catalog for Sentinel 2 tile.')
        return self.stac_client.get_files(
            collectionId=f'SENTINEL-2',
            spatial_extent=self.get_bbox(),
            temporal_extent=date_range,
            max_cloud_cover=max_cloud_cover,
            properties={'productType':f'S2MSI{level}', 'tileId': self.tile_id},
            limit=750
        )
        
    def is_tile_complete(self, image_metadata: Dict[str, Any]) -> bool:
        """
        Determine if the tile image is complete by comparing its area to the expected tile area.

        Parameters:
            image_metadata (Dict[str, Any]): The metadata of the image to check.

        Returns:
            bool: True if the image is complete (covers the entire tile), False otherwise.

        Example:
            >>> tile.is_tile_complete(image_metadata)
            True
        """
        return get_area(image_metadata.get('geometry')) >= (TILE_WIDTH * TILE_HEIGHT)
    
    def get_datacube(self, image_metadata: Dict[str, Any], max_cloud_cover: int, output_crs:int) -> openeo.DataCube:
        """
        Create and retrieve a datacube for the given image metadata.

        Parameters:
            image_metadata (Dict[str, Any]): The metadata of the image to be processed.
            max_cloud_cover (int): The maximum cloud cover for the datacube imagery.

        Returns:
            openeo.DataCube: The datacube object containing satellite data.

        Example:
            >>> datacube = tile.get_datacube(image_metadata, max_cloud_cover=10)
        """
        # Specifying the parameters for the imagery download.
        metadata = image_metadata['properties']
        self.log(f"{metadata['tileId']}, {metadata['datetime']}")
        bbox = image_metadata['bbox']
        self.openeo_client.authenticate_oidc_client_credentials()
        datacube = self.openeo_client.load_collection(                                                  # Specifying the parameters for the imagery download.
            "SENTINEL2_L2A",                                                                            # Satellite mission.
            temporal_extent=[metadata['start_datetime'], metadata['end_datetime']],                     # Date range.
            spatial_extent={"west": bbox[0], "east": bbox[2], "south": bbox[1], "north": bbox[3]},      # Area of interest.
            max_cloud_cover=max_cloud_cover,
            bands=[S2_Bands.RED.value, S2_Bands.GREEN.value, S2_Bands.BLUE.value, S2_Bands.NIR.value]
        )
        return datacube.resample_spatial(resolution=0, projection=output_crs, method='cubic')
    
    def download_datacube(self, target_datacube: openeo.DataCube, file_name: str, suffix: str) -> str:
        """
        Process and download the satellite imagery datacube as a GeoTIFF file.

        Parameters:
            target_datacube (openeo.DataCube): The datacube to be processed and downloaded.
            file_name (str): The base name of the file to be saved.
            suffix (str): A suffix to be appended to the file name.

        Returns:
            str: The file path where the downloaded and processed file is saved.

        Example:
            >>> datacube_file_path = tile.download_datacube(datacube, 'S2A_MSIL2A_20240819', 'RGB')
        """
        try:
            processed_file_path = f'{self.datacubes_dir}/{file_name}_{suffix}.GeoTIFF'

            self.log(f'[{self.tile_id}] {suffix}: Downloading satellite image {file_name}...')
            
            # Create a job for the datacube and download the results.
            job = target_datacube.create_job(out_format="GTiff", title="Sentinel2_MA")
            job.start_and_wait()
            job.get_results().download_file(target=processed_file_path)
            # This returns a proxy error
            # rgb.download(outputfile=file_path, format='GTiff', validate=False)
            self.log(f'[{self.tile_id}] {suffix}: Satellite image downloaded.')
            return processed_file_path
        except FileNotFoundError as fnf_error:
            self.log(f"File not found during datacube processing: {fnf_error}", logging.ERROR)
            raise
        except openeo.rest.OpenEoApiPlainError:
            self.log(f'[{self.tile_id}] ERROR. Retrying download in 5 seconds.', logging.WARNING)
            time.sleep(5)
            self.download_datacube(target_datacube, file_name, suffix)
        except Exception as e:
            self.log(f"Unexpected error: {e}", logging.ERROR)
            raise

    def process_bands(self, datacube: openeo.DataCube, file_name: str, bands: List[str], suffix: str, image_metadata:Dict[str, Any], enhancements:Dict[str,Any], remove_original: bool) -> bool:
        """
        Process the selected bands from the datacube and apply contrast enhancement.

        Parameters:
            datacube (openeo.DataCube): The datacube to process.
            file_name (str): The base name for the output file.
            bands (List[str]): The bands to filter from the datacube.
            suffix (str): Suffix to add to the output file.
            image_metadata (Dict[str,Any]): Metadata of the image to be processed.
            enhancements (Dict[str, Dict[str, int]]): Dictionary containing the enhancements to apply to the specific tile.
            remove_original (bool): Whether to remove the original downloaded file after processing.
            
        Returns:
            bool: If the image has been successfully enhanced.
        """
        self.log(f'[{self.tile_id}] Filtering bands: {suffix}')
        datacube_filtered = datacube.filter_bands(bands=bands)
        try:
            datacube_file_path = self.download_datacube(target_datacube=datacube_filtered, file_name=file_name, suffix=suffix)
            with open(datacube_file_path.replace('.GeoTIFF', '.json'), 'w') as metadata:
                json.dump(image_metadata, metadata, indent=4) 
            apply_contrast_enhancement(enhancements, input_file=datacube_file_path, output_dir=self.service_dir, suffix=suffix, area_name=self.region, date=image_metadata['properties']['start_datetime'])
            self.log(f'[{self.tile_id}] {suffix}: Satellite image enhanced.')
        except Exception as e:
            self.log(e)
            return False
        
        if remove_original:
            os.remove(datacube_file_path)
            self.log(f'[{self.tile_id}] Original file removed.')
        return True
    
    def download_and_enhance_COG(self, date_range: List[str], max_cloud_cover: int, output_crs:int, enhancements:Dict[str,Any], remove_original: Optional[bool] = True) -> None:
        """
        Query the catalog, download, and enhance satellite images, including RGB and NirGB bands.

        Parameters:
            date_range (List[str]): The time range for querying the catalog.
            max_cloud_cover (int): The maximum cloud cover for the images.
            output_crs (int): The CRS of the output COG file.
            enhancements (Dict[str, Dict[str, int]]): Dictionary contailing the enhancements to apply to the specific tile.
            remove_original (Optional[bool]): Whether to remove the original downloaded files after processing. Default is True.

        Example:
            >>> tile.download_and_enhance(date_range=[2024-01-01, 2024-12-31], max_cloud_cover=10)
        """
        only_complete = only_latest = True
        if os.getenv('ONLY_COMPLETE'):
            only_complete = True if os.getenv('ONLY_COMPLETE') == 'True' else False
        if os.getenv('ONLY_LATEST'):
            only_latest = True if os.getenv('ONLY_LATEST') == 'True' else False
        
        imagery = self.query_catalog(date_range=date_range, max_cloud_cover=max_cloud_cover)
        images_found = success_rgb = success_nirgb = False
        for image_metadata in imagery:
            images_found = True
            if not only_complete or (only_complete and self.is_tile_complete(image_metadata)):
                file_name = image_metadata['id'].replace('.SAFE', '')
                self.log(f'[{self.tile_id}] Processing image {file_name}')
                
                datacube = self.get_datacube(image_metadata, max_cloud_cover, output_crs)
                # Process RGB bands
                success_rgb = self.process_bands(datacube, file_name, S2_Bands.true_color_bands(), 'RGB', image_metadata, enhancements, remove_original)
                # Process NirGB bands
                success_nirgb = self.process_bands(datacube, file_name, S2_Bands.false_color_bands(), 'NirGB', image_metadata, enhancements, remove_original)
                if success_rgb and success_nirgb and only_latest:
                    break
        if success_rgb and success_nirgb:
            self.log(f'[{self.tile_id}] Image processing completed.')
        else:
            self.log(f'[{self.tile_id}] No complete image has been found for the date range {date_range}.')
        if not images_found:
            self.log(f'[{self.tile_id}] No images have been found for the date range {date_range}.')
    
    def download_raw(self, date_range: List[str], max_cloud_cover: int, s3_endpoint:Optional[str] = 'https://eodata.dataspace.copernicus.eu') -> None:
        only_complete = only_latest = True
        if os.getenv('ONLY_COMPLETE'):
            only_complete = True if os.getenv('ONLY_COMPLETE') == 'True' else False
        if os.getenv('ONLY_LATEST'):
            only_latest = True if os.getenv('ONLY_LATEST') == 'True' else False
        
        AWS = AWSService()
        imagery = self.query_catalog(date_range=date_range, max_cloud_cover=max_cloud_cover)
        images_found = False
        for image_metadata in imagery:
            images_found = True
            if not only_complete or (only_complete and self.is_tile_complete(image_metadata)):
                self.log(f'[{self.tile_id}] Instanciating AWS S3 service...')
                file_name = image_metadata['id'].replace('.SAFE', '')
                self.log(f'[{self.tile_id}] Downloading raw data for {file_name}')
                AWS.download_raw_product(image=image_metadata, endpoint=s3_endpoint)
                if only_latest:
                    break
                self.log(f'[{self.tile_id}] Raw product downlad completed.')
        if not images_found:
            self.log(f'[{self.tile_id}] No images have been found for the date range {date_range}.')
        
        
    """
    def get_images(self, date_range: List[str], max_cloud_cover: int, username:Optional[str] = None, password:Optional[str] = None, s3_client_id:Optional[str] = 'cdse-public', s3_token_endpoint:Optional[str] = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token') -> None:
        only_complete = True
        only_latest = True
        if os.getenv('ONLY_COMPLETE'):
            only_complete = True if os.getenv('ONLY_COMPLETE') == 'True' else False
        if os.getenv('ONLY_LATEST'):
            only_latest = True if os.getenv('ONLY_LATEST') == 'True' else False
        
        AWS = AWSService()
        gdal_images = []
        imagery = self.query_catalog(date_range=date_range, max_cloud_cover=max_cloud_cover)
        for image_metadata in imagery:
            if not only_complete or (only_complete and self.is_tile_complete(image_metadata)):
                self.log(f'[{self.tile_id}] Instanciating AWS S3 service...')
                token = AWS.get_token(s3_client_id, s3_token_endpoint, username, password)
                gdal_images.append(AWS.get_file(image_metadata['assets']['PRODUCT']['alternate']['s3']['href'], token))
                if only_latest:
                    break

        return gdal_images
    """