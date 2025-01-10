from datetime import datetime
import json
import os
from typing import Optional
from dotenv import load_dotenv
from joblib import Parallel, delayed


from src.Sentinel import SentinelTile
from src.SMTP import Email
from src.loggers import Logger

from src.utils import get_bbox, get_date_range, build_mosaic

def main_process(project_path:Optional[str] = os.getcwd(), send_email:Optional[bool] = False):
    # Load configurations from the environment file (.env)
    load_dotenv(override=True)

    # Configuration settings
    SERVICE_DIR = os.getenv('SERVICE_DIR')
    MAX_CLOUD_COVER = int(os.getenv('MAX_CLOUD_COVER')) or 5
    DAYS_OFFSET = int(os.getenv('DAYS_OFFSET')) or 30 # This must be enough so it detects an image with a valid cloud coverage!
    OUTPUT_CRS = os.getenv('OUTPUT_CRS') or 3857
    THREADS = int(os.getenv('THREADS')) or 2

    def execute_process(region_name, tile, enhancements):
        if get_bbox(tile) is not None:
            sentinel_tile = SentinelTile(
                region_name=region_name,
                tile_id=tile,
                catalog_url='https://catalogue.dataspace.copernicus.eu/stac/',
                openeo_url='https://openeo.dataspace.copernicus.eu',
            )
            
            sentinel_tile.logger = Logger(logger_name='src.Sentinel', level='DEBUG', handlers=['console', 'file'])
            sentinel_tile.download_and_enhance_COG(
                date_range=get_date_range(DAYS_OFFSET),
                max_cloud_cover=MAX_CLOUD_COVER,
                output_crs=OUTPUT_CRS,
                enhancements=enhancements,
                remove_original=True
            )
    
    # Process each tile in the spanish territory,
    # we run the tileset in a multithread so the process takes less time to complete.
    settings = None
    config_file = os.path.join(project_path, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as f:
            settings = json.load(f)
            for region_name, region in settings.items():
                Parallel(n_jobs=THREADS)(delayed(execute_process)(region_name, tile, region['enhancement_data']) for tile in region['tiles'])
    
    build_mosaic(f'{SERVICE_DIR}/RGB', 'RGB')
    build_mosaic(f'{SERVICE_DIR}/NirGB', 'NirGB')
    
    if send_email:
        today = datetime.today().strftime('%Y%m%d')
        # Send an email message once the process has finished
        email = Email()
        email.set_subject(os.getenv('SUBJECT'))
        email.add_content('Se ha completado la actualización del producto Sentinel-2 Máxima Actualidad.\n\nPara más detalles, consulte el fichero adjunto.')
        for file_name in os.listdir('logs'):
            if today in file_name:
                email.attach_file(filename=f'logs/{file_name}')
        return email.send(smtp_host=os.getenv('SMTP_HOST'), smtp_port=os.getenv('SMTP_PORT'), email_from=os.getenv('FROM'), password=None, email_to=os.getenv('TO'))