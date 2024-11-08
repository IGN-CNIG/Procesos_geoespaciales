import datetime
import json
import os
import re
import numpy as np
from typing import Optional, List, Dict, Tuple

from area import area
from osgeo import gdal


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


def get_area(feature:Dict[str, object]) -> float:
    """
    Calculates the area of a given GeoJSON feature using the `area` module.

    Parameters:
        feature (Dict[str, object]): A GeoJSON feature representing a polygon or multipolygon.

    Returns:
        float: The calculated area of the feature in square meters.

    Example:
        >>> geojson_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-73.981149, 40.7681], [-73.981149, 40.7681], [-73.979829, 40.7681], [-73.979829, 40.767344], [-73.981149, 40.7681]]]
                }
            }
        >>> get_area(geojson_feature)
        1234.56  # Area in square meters
    """
    return area(feature)

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

def get_geometry_envelope(tile_id:str) -> Tuple:
    """
    Get the geometry envelope (bounding box) from a GeoJSON string.
    
    Parameters:
        tile_id (str): A string representation of GeoJSON.
    
    Returns:
        tuple: (min_x, min_y, max_x, max_y) representing the bounding box.
    """
    # Load GeoJSON data
    with open('data/sentinel2-grid.geojson', 'r') as file:
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

                elif geometry['type'] == 'MultiPolygon':
                    # Iterate through each polygon
                    for polygon in coords:
                        for ring in polygon:
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

def apply_contrast_enhancement(enhancements:str, input_file:str, output_dir:str, area_name:str, date:str, suffix:str = 'RGB') -> None:
    """
    Apply contrast enhancement to an image file based on seasonal data.

    Parameters:
        enhancements (Dict[str, Dict[str, int]]): Dictionary containing the enhancements to apply to the specific tile.
        input_file (str): The path to the input image file.
        output_dir (str): The path to the root directory to store the output image.
        area_name (str): The name of the area for which to apply the enhancement.
        date (str): The date of the image in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'.
        suffix (str): The suffix to append to the output file name. Defaults to 'RGB'.

    Raises:
        FileNotFoundError: If the input file cannot be opened.
        ValueError: If any image band has no data.
    """
        
    if enhancements is not None:
        file_name = os.path.basename(input_file)
        gdal.UseExceptions()
        dataset = gdal.Open(input_file)
        if not dataset:
            raise FileNotFoundError(f"Unable to open {input_file}")
        num_bands = dataset.RasterCount
        # Create a new geotiff file where we are going to store the adjusted bands
        driver = gdal.GetDriverByName('GTiff')
        file_name = remove_dates_from_filename(file_name)
        corrected_file_path = f'{output_dir}/{file_name}'
        os.makedirs(os.path.dirname(corrected_file_path), exist_ok=True)
        out_dataset = driver.Create(corrected_file_path, dataset.RasterXSize, dataset.RasterYSize, num_bands, gdal.GDT_Byte) # The satellite images are returned in 16-bits, but we need an 8-bits imageº1
        out_dataset.SetProjection(dataset.GetProjection())
        out_dataset.SetGeoTransform(dataset.GetGeoTransform())
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
                    print(f'[{file_name}] Band {index}: Contrast enhancement applied')
                    # Scale 16 bits image to 8 bits image for the output
                    min_value = np.min(stretched_band)
                    max_value = np.max(stretched_band)
                    scaled_band = np.clip((band_data - min_value) / (max_value - min_value) * (255 - 0) + 0, 0, 255)
                    scaled_band = scaled_band.astype(np.uint8)
                    print(f'[{file_name}] Band {index}: Scale change to to 8-bits')
                    # Write to the output dataset
                    out_band = out_dataset.GetRasterBand(index)
                    out_band.WriteArray(scaled_band)
                    #out_band.SetNoDataValue(0)
                else:
                    os.remove(corrected_file_path)
                    raise ValueError(f'Could not read the band {index}, image potentially faulty.')
            except:
                os.remove(corrected_file_path)
                raise ValueError(f'The band {index} has no data, image could be faulty.')
        # After we've finished writing the output file, we clean the memory
        band_data = None
        dataset = None
        out_dataset = None