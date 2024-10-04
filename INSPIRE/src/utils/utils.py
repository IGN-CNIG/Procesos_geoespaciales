from typing import List, Optional, Tuple, Any, Generator
from datetime import datetime, timedelta

from functools import reduce
import requests
import xmltodict


def deep_get(dictionary, keys:str, default:Optional[str]=None) -> Any:
    """
    Getter for iterating over a dictionary with the specified path (keys), this avoids Exceptions when a path does not exist

    Args:
        keys (str): Path for the value we need to get, with the attributes separated with slash (e.g. gn:NamedPlace/gn:inspireId/base:Identifier/base:localId)
        default (Optional[str], optional): Value to return if the path does not exist. Defaults to None.

    Returns:
        Any: Value for the specified path. It can be any type (e.g. string, number, array, dict...)
    """
    result = reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("/"), dictionary)
    if result == {'@xsi:nil': 'true'}:
        result = None
    return result if not isinstance(result, dict) else [result]

def request(url: str) -> Optional[str]:
    """
    Request XML metadata from the specified URL.

    Parameters:
        url (str): URL for the Capabilities metadata.

    Returns:
        Optional[str]: The response text if successful; otherwise, raises an exception.
    """
    try:
        response = requests.get(url, timeout=10000)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # Parse and check for errors in the XML
        try:
            parsed_xml = xmltodict.parse(response.text)
            error = deep_get(parsed_xml, 'ows:ExceptionReport/ows:Exception')
            if error:
                raise ValueError(f"OWS Exception: {error}")

            return response.text

        except Exception as parse_error:
            raise ValueError(f"Error parsing XML response: {parse_error}")

    except requests.exceptions.RequestException as req_error:
        raise ConnectionError(f"Error during request: {req_error}")
            

VALID_DATE_FORMATS = ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']

def day_ranges(start_date: str, end_date: str, n: Optional[int] = 1) -> Generator[Tuple[datetime, datetime], None, None]:
    """
    Generates date ranges of `n` days between the specified start and end dates.

    Parameters:
        start_date (str): The start date in string format.
        end_date (str): The end date in string format.
        n (int): The number of days in each range.

    Yields:
        (Tuple[datetime, datetime]): A tuple containing the start and end of each date range.
    """
    # Validate the 'n' parameter
    if n <= 0:
        raise ValueError("The interval 'n' must be a positive integer.")

    date_format = get_date_format(start_date)
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    interval = timedelta(days=n)

    period_start = start
    while period_start < end:
        period_end = min(period_start + interval, end)
        yield (period_start, period_end)
        period_start = period_end

"""https://stackoverflow.com/questions/51293632/how-do-i-divide-a-date-range-into-months-in-python"""
def month_ranges(begin: str, end: str) -> Generator[List[datetime], None, None]:
    """
    Generates month ranges between the specified begin and end dates.

    Parameters:
        begin (str): The start date in string format.
        end (str): The end date in string format.

    Yields:
        (Tuple[datetime, datetime]): A list containing the start and end of each month.
    """
    date_format = get_date_format(begin)
    begin_date = datetime.strptime(begin, date_format)
    end_date = datetime.strptime(end, date_format)

    while begin_date <= end_date:
        next_month = begin_date.replace(day=1) + timedelta(days=31)  # Move to the next month
        next_month = next_month.replace(day=1)
        if next_month > end_date:
            yield [begin_date, last_day_of_month(begin_date)]
            break
        yield (begin_date, last_day_of_month(begin_date))
        begin_date = next_month

def last_day_of_month(date: datetime) -> datetime:
    """
    Calculates the last day of the month for the given date.

    Parameters:
        date (datetime): The date for which to find the last day of the month.

    Returns:
        datetime: The last day of the month.
    """
    next_month = date.replace(day=28) + timedelta(days=4)  # Ensure we go to the next month
    return next_month - timedelta(days=next_month.day)  # Go back to the last day of the month

def is_date(value: str) -> bool:
    """
    Checks if the given string value matches any of the valid date formats.

    Parameters:
        value (str): The date string to validate.

    Returns:
        bool: True if the value matches any valid date format, False otherwise.
    """
    return any(validate(value, fmt) for fmt in VALID_DATE_FORMATS)

def get_date_format(value: str) -> Optional[str]:
    """
    Determines the date format of the given string value.

    Parameters:
        value (str): The date string whose format needs to be determined.

    Returns:
        Optional[str]: The date format if matched, otherwise None.
    """
    for fmt in VALID_DATE_FORMATS:
        if validate(value, fmt):
            return fmt
    return None

def validate(value: str, pattern: str) -> bool:
    """
    Validates if the given string value matches the specified date format.

    Parameters:
        value (str): The date string to validate.
        pattern (str): The date format to validate against.

    Returns:
        bool: True if the value matches the format, False otherwise.
    """
    try:
        datetime.strptime(value, pattern)
        return True
    except ValueError:
        return False