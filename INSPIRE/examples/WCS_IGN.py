import os

from src.modules.inspire import WCSService


def main() -> None:
        
    # 1. Read features from the service service
    # Mapa Base
    name = 'Mapa Base'
    wcs = WCSService(source='https://servicios.idee.es/wcs-inspire/mdt', name=name, version='2.0.1', timeout=90)
    info = wcs.capabilities.get_service_info()
    operations = wcs.capabilities.get_operations()
    formats = wcs.capabilities.get_supported_formats()
    coverages = wcs.capabilities.list_coverages()
    first_coverage = list(coverages.keys())[0]
    description = wcs.capabilities.describe_coverage(coverageID=first_coverage)
    
    # version 1.0.0
    # raster = wcs.get_coverage(filename=f'{os.getcwd()}/output/prueba.TIFF', coverage='Elevacion4258_5', crs='EPSG:4326', bbox='-3.70379,40.41678,-3.70329,40.41728', width=256, height=256, format='image/tiff')
    # version 2.0.1
    raster = wcs.get_coverage(filename=f'{os.getcwd()}/output/prueba.TIFF', coverageID='Elevacion4258_5', subset=['x(-3.70379,-3.70329)', 'y(40.41678,40.41728)'], format='image/tiff')
    print(raster)
    
if __name__ == '__main__':
    main()