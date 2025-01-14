import datetime
import json
import os
from pathlib import Path
import re
import numpy as np
from typing import Optional, List, Dict, Tuple, Any

from area import area
from osgeo import gdal

AREA_TOLERANCE = 0.05

def get_dates_from_filename(filename:str) -> List[str]:
    """
    Gets date information from a filename. The date format can be YYYYMMDD or YYYYMMDDTHHMMSS.

    Parameters:
        filename (str): The original filename containing the date.

    Returns:
        List[str]: List of the dates found in the filename.

    Example:
        >>> remove_dates_from_filename("file_20230101T123456_data.txt")
        ['20230101T123456']
    """
    # RegEx to find dates in YYYYMMDD or YYYYMMDDTHHMMSS format.
    date_pattern = r'\d{8}(T\d{6})?'
    
    return re.findall(date_pattern, filename)

def remove_dates_from_filename(filename:str) -> str:
    """
    Removes date information from a filename. The date format can be YYYYMMDD or YYYYMMDDTHHMMSS.

    Parameters:
        filename (str): The original filename containing the date.

    Returns:
        str: The cleaned filename with the date removed and extra underscores minimized.

    Example:
        >>> remove_dates_from_filename("file_20230101T123456_data.txt")
        'file_data.txt'
    """
    # RegEx to find dates in YYYYMMDD or YYYYMMDDTHHMMSS format.
    date_pattern = r'\d{8}(T\d{6})?'
    
    # Replace the found date by an empty string
    cleaned_filename = re.sub(date_pattern, '', filename)
    
    # Return the clean name, removing the additional _
    return re.sub(r'_+', '_', cleaned_filename).strip('_')


def is_tile_complete(tile_id:str, bbox: Dict[str, Any], datetime:str) -> bool:
    """
    Determine if the tile image is complete by comparing its area to the expected tile area.

    Parameters:
        tile_id (str): The tile id to check its geometry in the grid file.
        bbox (Dict[str, Any]): The bbox for the tiled image to check.
        datetime(str): Datetime for the tiled image capture.

    Returns:
        bool: True if the image is complete (covers the entire tile), False otherwise.

    Example:
        >>> is_tile_complete('30SYH', [-0.727635807400437, 37.8068570326715, 0.566452796705863, 38.8262817087051], 2024-12-25T10:54:51.024000Z)
        True
    """
    tile_bbox = get_bbox(tile_id)
    tile_geojson = {
        "type": "Polygon",
        "coordinates": [[
            [tile_bbox[0], tile_bbox[1]],  # Bottom-left
            [tile_bbox[2], tile_bbox[1]],  # Bottom-right
            [tile_bbox[2], tile_bbox[3]],  # Top-right
            [tile_bbox[0], tile_bbox[3]],  # Top-left
            [tile_bbox[0], tile_bbox[1]]   # Close the polygon
        ]]
    }
    image_geojson = {
        "type": "Polygon",
        "coordinates": [[
            [bbox[0], bbox[1]],  # Bottom-left
            [bbox[2], bbox[1]],  # Bottom-right
            [bbox[2], bbox[3]],  # Top-right
            [bbox[0], bbox[3]],  # Top-left
            [bbox[0], bbox[1]]   # Close the polygon
        ]]
    }
    
    tile_size = area(tile_geojson)/(1000*1000)
    image_size = area(image_geojson)/(1000*1000)
                
    print(f'[{tile_id}] Date: {datetime}, Tile size: {tile_size}, Image size: {image_size}')
    return round(image_size, 2) >= (round(tile_size, 2) - round(tile_size*AREA_TOLERANCE, 2))

def get_date_range(days:int) -> List[str]:
    """
    Calculate a date range starting from 'days' days ago to today.

    Parameters:
        days (int): The number of days to go back from today.

    Returns:
        list: A list containing the start date and today's date in ISO format.
    """
    today = datetime.datetime.now()
    delta = datetime.timedelta(days = days)
    start = today - delta
    return [start.isoformat(), today.isoformat()]

def get_season(date_str) -> Dict[str, Dict[str, int]]:
    """
    Determine the season of a given date string.

    Parameters:
        date_str (str): The date as a string in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'.

    Returns:
        str: The name of the season for the provided date.

    Raises:
        ValueError: If the date string is not in the expected format.
    """

    # Convert the date string to a datetime.date object
    date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()

    # Define the start dates for each season
    year = date.year
    spring_start = datetime.date(year, 3, 20)
    summer_start = datetime.date(year, 6, 21)
    autumn_start = datetime.date(year, 9, 22)
    winter_start = datetime.date(year, 12, 21)

    # Determine the season
    if spring_start <= date < summer_start:
        return 'Spring'
    elif summer_start <= date < autumn_start:
        return 'Summer'
    elif autumn_start <= date < winter_start:
        return 'Autumn'
    else:
        return 'Winter'

def get_bbox(tile_id:str) -> Tuple:
    """
    Get the geometry envelope (bounding box) from a GeoJSON string.
    
    Parameters:
        tile_id (str): A string representation of GeoJSON.
    
    Returns:
        tuple: (min_x, min_y, max_x, max_y) representing the bounding box.
    """
    # Load GeoJSON data
    path = Path(os.path.dirname(__file__)).parent
    with open(f'{path}/data/sentinel2-grid.geojson', 'r') as file:
        geojson = json.load(file)
    
    # Initialize bounding box coordinates
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    # Loop through features to find the matching tile_id
    for feature in geojson['features']:
        if feature['properties']['Name'] == tile_id:
            # Extract geometries from the feature
            geometries = feature['geometry']['geometries']

            # Loop through each geometry
            for geometry in geometries:
                coords = geometry['coordinates']
                
                # Check if it's a Polygon or MultiPolygon
                if geometry['type'] == 'Polygon':
                    # Iterate through each ring (the first ring is the outer boundary)
                    for ring in coords:
                        for point in ring:
                            x, y = point[0], point[1]
                            min_x = min(min_x, x)
                            min_y = min(min_y, y)
                            max_x = max(max_x, x)
                            max_y = max(max_y, y)

            # Return the bounding box as a tuple
            return (min_x, min_y, max_x, max_y)

    # If the tile_id is not found, return None
    return None

def save_date_to_footprint(tile_id:str, image_metadata:Dict, service_dir:str) -> None:
    grid_path = f'{service_dir}/Grid.geojson'
    grid = {
        "type": "FeatureCollection",
        "features": []
    }
    tile_found = False
    if os.path.exists(grid_path):
        with open(grid_path, 'r') as file:
            grid = json.load(file)
            for tile in grid.get('features'):
                if tile.get('properties').get('Name') == tile_id:
                    tile_found = True
                    tile['properties']['Date'] = image_metadata.get('properties').get('datetime')
                    tile['properties']['CloudCover'] = image_metadata.get('properties').get('cloudCover')
                    tile['properties']['ProcessingLevel'] = image_metadata.get('properties').get('processingLevel')
    if not tile_found:
        path = Path(os.path.dirname(__file__)).parent
        with open(f'{path}/data/sentinel2-grid.geojson', 'r') as file:
            geojson = json.load(file)
            tiles = [tile for tile in geojson.get('features') if tile.get('properties').get('tileId') == tile_id]
            if len(tiles) > 0:
                grid.get('features').append({
                    "type": "Feature",
                    "properties": {
                        "Name": tile_id,
                        "Date": image_metadata.get('properties').get('datetime'),
                        "CloudCover": image_metadata.get('properties').get('cloudCover'),
                        "ProcessingLevel": image_metadata.get('properties').get('processingLevel')
                    },
                    "geometry": tiles[0].get('geometries')[0]
                })
                        
    with open(f'{service_dir}/Grid.geojson', 'w') as file:
        json.dump(grid, file, indent=4, ensure_ascii=False)
        
def cumulative_count_cut(band:np.matrix, min_percentile:Optional[int]=2, max_percentile:Optional[int]=98) -> tuple:
    """
    Apply cumulative count cut on min/max values similar to QGIS.

    Parameters:
        band (np.matrix): The matrix of band data (e.g., from an image).
        min_percentile (Optional[int]): The minimum percentile for cutting. Defaults to 2.
        max_percentile (Optional[int]): The maximum percentile for cutting. Defaults to 98.

    Returns:
        tuple: A tuple containing the minimum and maximum values after applying the cut.
    """
    # https://gis.stackexchange.com/questions/481083/cumulative-count-cut-min-max-values-in-python-different-from-min-max-values-in-q
    min_val = np.nanpercentile(band, min_percentile)
    max_val = np.nanpercentile(band, max_percentile)
    return (min_val,max_val)

def apply_contrast_enhancement(enhancements:str, input_file:str, output_dir:str, output_name:str, date:str, suffix:str = 'RGB') -> None:
    """
    Apply contrast enhancement to an image file based on seasonal data.

    Parameters:
        enhancements (Dict[str, Dict[str, int]]): Dictionary containing the enhancements to apply to the specific tile.
        input_file (str): The path to the input image file.
        output_dir (str): The path to the root directory to store the output image.
        output_name (str): The name of the output file.
        area_name (str): The name of the area for which to apply the enhancement.
        date (str): The date of the image in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'.
        suffix (str): The suffix to append to the output file name. Defaults to 'RGB'.

    Raises:
        FileNotFoundError: If the input file cannot be opened.
        ValueError: If any image band has no data.
    """
        
    if enhancements is not None:
        
        gdal.UseExceptions()
        dataset = gdal.Open(input_file)
        if not dataset:
            raise FileNotFoundError(f"Unable to open {input_file}")
        num_bands = dataset.RasterCount
        # Create a new geotiff file where we are going to store the adjusted bands
        corrected_file_path = f'{output_dir}/TEMP_{output_name}'
        corrected_file_path_COG = f'{output_dir}/{output_name}'.replace('.GeoTIFF', '.tif')

        os.makedirs(os.path.dirname(corrected_file_path), exist_ok=True)
        driver = gdal.GetDriverByName('GTiff')
        
        black_pixel_mask = None
        for index in range(1, num_bands + 1):
            band = dataset.GetRasterBand(index)
            band_data = band.ReadAsArray()
            band_mask = band_data == 0
            black_pixel_mask = band_mask if black_pixel_mask is None else (black_pixel_mask & band_mask)

        # Step 2: Create an alpha band based on the black pixel mask
        alpha_band = np.where(black_pixel_mask, 0, 255).astype(np.uint8)  # Transparent (0) for black pixels, opaque (255) otherwise
        
        # Step 3: Modify the output dataset to include the alpha band
        out_dataset = driver.Create(corrected_file_path, dataset.RasterXSize, dataset.RasterYSize, num_bands + 1, gdal.GDT_Byte) # The satellite images are returned in 16-bits, but we need an 8-bits imageº1
        out_dataset.SetProjection(dataset.GetProjection())
        out_dataset.SetGeoTransform(dataset.GetGeoTransform())
        
        # Write the alpha band to the last band of the output dataset
        out_alpha_band = out_dataset.GetRasterBand(num_bands + 1)
        out_alpha_band.WriteArray(alpha_band)
        out_alpha_band.SetNoDataValue(0)
        
        # Look for the new min and max for the stretch, depending on the season of the year the images are taken
        new_min = -32768
        new_max = 32767
        season = get_season(date)
        enhancement = enhancements[season]
        new_min, new_max = (enhancement[suffix]['min'], enhancement[suffix]['max'])
        # For each band, we perform the adjustments
        for index in range(1, num_bands + 1):
            band = dataset.GetRasterBand(index)
            try:
                band_data = band.ReadAsArray()
                if len(band_data) > 0:
                    # Calculate min and max values for origin file
                    band_min, band_max = cumulative_count_cut(band_data)
                    # Apply custom StretchToMinimumMaximum algorithm similar to QGIS
                    stretched_band = np.clip(((band_data - band_min) / (band_max - band_min)) * (new_max - new_min) + new_min, new_min, new_max)
                    print(f'[{output_name}] Band {index}: Contrast enhancement applied')
                    # Scale 16 bits image to 8 bits image for the output
                    min_value = np.min(stretched_band)
                    max_value = np.max(stretched_band)
                    scaled_band = np.clip((band_data - min_value) / (max_value - min_value) * (255 - 0) + 0, 0, 255)
                    scaled_band = scaled_band.astype(np.uint8)
                    print(f'[{output_name}] Band {index}: Scale change to to 8-bits')
                    # Write to the output dataset
                    out_band = out_dataset.GetRasterBand(index)
                    out_band.WriteArray(scaled_band)
                    out_band.SetNoDataValue(0)
                else:
                    raise ValueError(f'Could not read the band {index}, image potentially faulty.')
            except:
                raise ValueError(f'The band {index} has no data, image could be faulty.')
        
        if out_dataset is not None:
            options = gdal.TranslateOptions(
                format="COG",
                creationOptions=[
                    f"TILING_SCHEME=GoogleMapsCompatible",
                    f"COMPRESS=LZW"
                ],
                metadataOptions={
                    "TIFFTAG_DATETIME": date
                }
            )
            try:
                # Perform the translation
                gdal.Translate(destName=corrected_file_path_COG, srcDS=out_dataset, options=options)
                print(f'[{output_name}] COG created successfully: {corrected_file_path_COG}')
                os.remove(corrected_file_path)
            except Exception as e:
                print(f"Error al ejecutar gdal.Translate: {e}")

        # After we've finished writing the output file, we clean the memory
        band_data = None
        dataset = None
        out_dataset = None


def build_mosaic(cog_directory: str, suffix:str, resolution:int) -> None:
    """
    Creates a mosaic from Cloud Optimized GeoTIFF (COG) files in a specified directory.

    This function combines multiple COG files with a given suffix into a single mosaic.
    The mosaic is first created as a Virtual Raster (VRT) and then translated into a 
    Cloud Optimized GeoTIFF (COG) using GDAL.

    Parameters:
        cog_directory (str): The directory containing the input COG files.
        suffix (str): The suffix to filter input COG files (e.g., 'RGB' will match files ending with '_RGB.tif').
        resolution (float): The target resolution in map units (e.g., meters per pixel). If None, keeps original resolution.

    Outputs:
        - A COG file named `mosaic_<suffix>.tif` in the input directory.

    Notes:
        - The output COG file uses the "GoogleMapsCompatible" tiling scheme and LZW compression.
        - Metadata includes the current datetime in the TIFFTAG_DATETIME field.

    Example:
        build_mosaic("/path/to/cog/files", "RGB")
        This will create:
        - `/path/to/cog/files/mosaic_RGB.tif`
    """
    if os.path.exists(cog_directory) and len(os.listdir(cog_directory)) > 0:
        # Output files
        vrt_output = f'{cog_directory}/mosaic_{suffix}_{resolution}.vrt'
        COG_output = f'{cog_directory}/mosaic_{suffix}_{resolution}.tif'

        # List all COG files in the directory
        cog_files = [os.path.join(cog_directory, f) for f in os.listdir(cog_directory) if f.endswith(f'{suffix}.tif')]
        cog_files = sorted(cog_files, key=lambda x: x[1], reverse=True)

        # Build the VRT (Virtual Raster)
        gdal.BuildVRT(vrt_output, cog_files)
        
        options = None
        
        # Adjust resolution if specified
        if resolution is not None:
            options = gdal.TranslateOptions(
                format="COG",
                creationOptions=[
                    "TILING_SCHEME=GoogleMapsCompatible",
                    "COMPRESS=LZW",
                    "BIGTIFF=YES"
                ],
                metadataOptions={
                    "TIFFTAG_DATETIME": datetime.datetime.now().isoformat()
                },
                xRes=resolution,
                yRes=resolution
            )
        else:
            options = gdal.TranslateOptions(
                format="COG",
                creationOptions=[
                    "TILING_SCHEME=GoogleMapsCompatible",
                    "COMPRESS=LZW",
                    "BIGTIFF=YES"
                ],
                metadataOptions={
                    "TIFFTAG_DATETIME": datetime.datetime.now().isoformat()
                }
            )

        # Translate the VRT to a GeoTIFF
        gdal.Translate(destName=COG_output, srcDS=vrt_output, options=options)
        
        if os.path.exists(COG_output):
            os.remove(vrt_output)
            print(f'[{COG_output}] Mosaic created successfully.')
        else:
            print(f'[{COG_output}] Error in mosaic generation, file not created.')
