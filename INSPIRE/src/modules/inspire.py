"""
GPL License Disclaimer:
------------------------
This software is licensed under the GNU General Public License (GPL). You are free to redistribute 
and/or modify this software under the terms of the GPL as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without 
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, 
see https://www.gnu.org/licenses/.

Data Source:
------------
This module utilizes geographic data provided by multiple organizations under the conditions of 
use as outlined in the applicable licenses.

Contact:
--------
For more information about the terms of use or to request specific data, please contact:

Centro Nacional de Información Geográfica (CNIG)
IGN-CNIG, España
Calle General Ibáñez de Ibero, 3
28003 Madrid, España

Teléfono: +34 913 495 000

Website: https://www.cnig.es/

Email: consulta@cnig.es

"""

import io
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Generator
import sys

from bs4 import BeautifulSoup
from osgeo import ogr, gdal
import requests
from zipfile import ZipFile


from src.modules.capabilities import WFSCapabilities, WCSCapabilities, OpenAPIDoc
import src.utils.utils as utils

from src.utils.constants import WFS_PARAMETERS, WCS_PARAMETERS


os.environ['GDAL_DATA'] = gdal.GetConfigOption('GDAL_DATA') or Path(sys.executable).parent.as_posix() + r'\Library\share\gdal'
os.environ['PROJ_LIB'] = gdal.GetConfigOption('PROJ_LIB') or Path(sys.executable).parent.as_posix() + r'\Library\share\proj'

# import _pydevd_bundle.pydevd_constants
# _pydevd_bundle.pydevd_constants.PYDEVD_WARN_EVALUATION_TIMEOUT = 30. # seconds

class InspireDownloadService:
    """
    Base class for INSPIRE (Infrastructure for Spatial Information in Europe) download services.
    Handles common functionality for accessing and processing geospatial data from various service types.

    Attributes:
        logger (logging.Logger): Logger instance used for logging events and errors.
        source (str): The URL or source of the service.
        name (str): The name of the service.
        service (str): The type of service (e.g., WFS, ATOM).
        version (Optional[str]): The version of the service, if applicable.
        allow_paging (Optional[bool]): Indicates if paging is allowed for fetching data.
        max_features (Optional[int]): Maximum number of features to fetch.
        timeout (int): Timeout setting for requests in seconds.
        ds (Optional[ogr.DataSource]): The data source object for interacting with geospatial data.
        summary (list[Optional[dict]]): Summary list for storing metadata about fetched features.

    Methods:
        log(cls, message: str, level: Optional[int] = logging.INFO) -> None:
            Logs a message at the specified logging level.

        _set_ds(self, data_source: ogr.DataSource) -> None:
            Sets the data source object for the service.

        _SQL_filter_on_ds(self, data_source: ogr.DataSource, index: int, SQL_PREDICATE: str) -> Generator[ogr.Feature, None, None]:
            Filters features in a data source using an SQL predicate.

        add_errors_to_feature(self, feature: ogr.Feature) -> None:
            Adds error information to a feature if it fails validation checks.
    """
    logger:logging.Logger = logging.getLogger(__name__)  # Obtain a logger for this module/class
    source: str
    name: str
    service: str
    version:Optional[str] = None # = '2.0.0'
    allow_paging: Optional[bool] = True # = True <- If the service capabilities allow paging, this is taken into account.
    max_features: Optional[int] = -1 # = 5000 FEATURES <- If we increase this number, it stops recognizing the fields in ExecuteSQL
    timeout: int = 90 # = 90 SECONDS <- This avoids the timeout error (504) when too many features
    ds: Optional[ogr.DataSource] = None
    summary: list[Optional[dict]] = []

    def __init__(self, service) -> None:
        """
        Initializes the InspireDownloadService with the specified service type.

        Parameters:
            service (str): The type of service (e.g., WFS, ATOM).
        """
        self.service = service
        ogr.DontUseExceptions()
    
    @classmethod
    def log(cls, message:str, level:Optional[str] = logging.INFO) -> None:
        """
        Logs a message at the specified logging level if the logger is active, otherwise prints it in console.

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

    def _set_ds(self, data_source):
        """
        Sets the data source object for the service.

        Parameters:
            data_source (ogr.DataSource): The data source to use for fetching geospatial data.
        """
        self.ds = data_source

    def _SQL_filter_on_ds(self, data_source:ogr.DataSource, index:int, SQL_PREDICATE:str) -> Generator[ogr.Feature, None, None]:
        """
        Filters features in a data source using an SQL predicate.

        Parameters:
            data_source (ogr.DataSource): The data source to query.
            index (int): The index of the layer to filter.
            SQL_PREDICATE (str): The SQL predicate to apply.

        Yields:
            ogr.Feature: The filtered features that match the SQL predicate.
        """
        if data_source:
            layer = data_source.GetLayerByIndex(index).GetName().split(':')[1] if len(data_source.GetLayerByIndex(index).GetName().split(':')) == 2 else data_source.GetLayerByIndex(index).GetName()
            query = f'SELECT * FROM {layer} WHERE {SQL_PREDICATE}'
            sql_lyr = data_source.ExecuteSQL(query, None)
            if sql_lyr:
                self.log(f'Query: {query}')
                self.log(f'Features found: {sql_lyr.GetFeatureCount()}')
                if sql_lyr and sql_lyr.GetFeatureCount() > 0:
                    if self.service == 'WFS':
                        if self.capabilities.query_constraint('CountDefault'):
                            self.max_features = int(self.capabilities.query_constraint('CountDefault').get('default_value'))
                        if sql_lyr.GetFeatureCount() >= self.max_features and not self.capabilities.query_constraint('ImplementsResultPaging').get('default_value').upper() == 'TRUE':
                            self.log('Max number of features has been reached. Please, contact your data provider to request results paging.', logging.WARNING)
                    for feature in sql_lyr:
                        self.add_errors_to_feature(feature)
                        yield feature
                
                data_source.ReleaseResultSet(sql_lyr)

    def add_errors_to_feature(self, feature:ogr.Feature) -> None:
        """
        Adds error information to a feature if it fails validation checks.

        Parameters:
            feature (ogr.Feature): The feature to validate and add error information to.
        """
        self.log(f'Validating feature {feature.GetFieldAsString(0)}', logging.DEBUG)
        if not feature.Validate():
            feature.errors = {'Unique': [], 'Nullable': []}
            for index in  range(feature.GetFieldCount()):
                field = feature.GetField(index)
                definition = feature.GetDefnRef().GetFieldDefn(index)
                if field is None and not definition.IsNullable():
                    feature.get('errors').get('nullable').add(definition.name)


class WFSService(InspireDownloadService):
    """ 
    Represents an Inspire WFS (Web Feature Service) Download Service for fetching geographical features.

    This class allows users to interact with a WFS service, retrieve its capabilities, fetch features based on stored queries, and handle geospatial data operations.
    
    Attributes:
        source (str): The URL of the WFS service endpoint.
        name (str): A name for identifying the WFS service instance.
        version (Optional[str]): The WFS protocol version to use (default is '2.0.0').
        max_features (Optional[int]): Maximum number of features to retrieve in a single request (default is 5000).
        timeout (Optional[int]): Timeout duration in seconds for requests to the WFS service (default is 90).
        capabilities (Capabilities): An instance representing the capabilities of the WFS service.
        stored_queries (dict): A dictionary holding stored queries available in the WFS service.
    
    ## Methods
        get_feature_from_stored_query(self, STORED_QUERY:str, **args) -> Generator[ogr.Feature, None, None]:
            Fetches features from the WFS service using a stored query.
        get_feature_parameters(self) -> Dict[str, bool]:
            Retrieves the feature parameters supported by the WFS service for the given version.
        get_feature(self, SQL_PREDICATE:Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]:
            Fetches features from the WFS service based on specified parameters.
    """
    def __init__(self, source:str, name:str, version:Optional[str] = '2.0.0', max_features:Optional[int] = 5000, timeout:Optional[int] = 90) -> None:
        """
        Initializes a WFSService instance with specified parameters.

        Parameters:
            source (str): The URL of the WFS service endpoint.
            name (str): A name to identify the WFS service.
            version (Optional[str], optional): The WFS protocol version to use (default is '2.0.0').
            max_features (Optional[int], optional): Maximum number of features to retrieve per request (default is 5000).
            timeout (Optional[int], optional): Timeout for WFS requests in seconds (default is 90).
        """
        InspireDownloadService.__init__(self, service='WFS')
        self.source = source.replace('?', '')
        self.name = name
        self.version = version
        self.max_features = max_features
        self.timeout = timeout
        self.__capabilities = WFSCapabilities(self.service, self.version, self.source)
        data_source = ogr.Open(f'WFS:{self.source + f"?service=WFS&version={self.version}&request=GetFeature"}')
        super()._set_ds(data_source=data_source)
        self.log(f'WFS {name} service READING STARTED')

    def get_feature_from_stored_query(self, STORED_QUERY=str, **args) -> Generator[ogr.Feature, None, None]:
        """
        Fetches features from the WFS service using a stored query.

        Parameters:
            STORED_QUERY (str): The identifier of the stored query to execute.
            **args: Additional parameters to pass to the stored query.

        Yields:
            ogr.Feature: Features returned by the stored query.

        Raises:
            ValueError: If the stored query does not exist.
        """
        if self.capabilities.stored_queries.get(STORED_QUERY):
            url = self.source + f'?service=WFS&version={self.version}&request=GetFeature&STOREDQUERY_ID={self.capabilities.stored_queries.get(STORED_QUERY).identifier}'
            for parameter in args:
                if self.capabilities.stored_queries.get(STORED_QUERY).has_parameter(parameter):
                    url += f"&{parameter}={args.get(parameter)}"
                else:
                    self.log(f'The parameter {parameter} is not found in the Stored Query {STORED_QUERY}', logging.WARNING)
                    
            ds = ogr.Open(f'WFS:{url}')
            if ds and ds.GetLayerCount() > 0 and ds.GetLayer().GetFeatureCount() > 0:
                for feature in ds.GetLayer():
                    super().add_errors_to_feature(feature)
                    yield feature
        else:
            print('The stored query {stored_query} does not exist.')

    def get_feature_parameters(self) -> Dict[str, bool]:
        """
        Retrieves the feature parameters supported by the WFS service for the given version.

        Returns:
            (Dict[str, bool]): A dictionary of feature parameters and their availability (True/False).
        """
        return WFS_PARAMETERS.get(self.version)

    def get_feature(self, SQL_PREDICATE:Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]:
        """
        Fetches features from the WFS service based on specified parameters.

        Parameters:
            SQL_PREDICATE (Optional[str]): SQL predicate to filter features (default is None).
            **args: Additional parameters for the GetFeature request.

        Yields:
            ogr.Feature: Features that match the specified parameters.

        Raises:
            ValueError: If mandatory parameters are missing.
        """
        # https://gdal.org/api/python/vector_api.html
        parameters = self.get_feature_parameters()
        missing = [key for (key, value) in parameters.items() if value.get('required') and not args.get(key) and not key in ['service', 'request', 'version']]
        if len(missing) == 0:
            not_valid_params = []
            url = self.source + f'?service=WFS&version={self.version}&request=GetFeature'
            for arg in args:
                if arg in parameters:
                    url += f'&{arg.upper()}={args.get(arg)}'
                else:
                    not_valid_params.append(arg)
            if len(not_valid_params) > 0:
                self.log(f'The following parameters have been excluded: {not_valid_params}\nValid params for WFS version {self.version} are: {list(parameters.keys())}', logging.WARNING)
            
            data_source = ogr.Open(f'WFS:{url}')
            if data_source is not None:
                for index in range(data_source.GetLayerCount()):
                    if SQL_PREDICATE:
                        yield from super()._SQL_filter_on_ds(data_source=data_source, index=index, SQL_PREDICATE=SQL_PREDICATE)
                    else:
                        self.log(f'Features found: {data_source.GetLayerByIndex(index).GetFeatureCount()}')
                        for feature in data_source.GetLayerByIndex(index):
                            super().add_errors_to_feature(feature)
                            yield feature
        else:
            self.log(f'The following mandatory parameters are missing: {missing}', logging.CRITICAL)
            raise ValueError(f'The following mandatory parameters are missing: {missing}')
        
    @property
    def capabilities(self):
        return self.__capabilities


class WCSService(InspireDownloadService):
    """ 
    Represents an Inspire WCS (Web Coverage Service) Download Service for fetching geographical coverages.

    This class allows users to interact with a WCS service, retrieve its capabilities, fetch coverages based on parameters, and handle geospatial data operations.
    
    Attributes:
        source (str): The URL of the WCS service endpoint.
        name (str): A name for identifying the WCS service instance.
        version (Optional[str]): The WCS protocol version to use (default is '2.0.1').
        max_coverages (Optional[int]): Maximum number of coverages to retrieve in a single request (default is 100).
        timeout (Optional[int]): Timeout duration in seconds for requests to the WCS service (default is 90).
        capabilities (Capabilities): An instance representing the capabilities of the WCS service.
        
    ## Methods
        get_coverage_parameters(self) -> Dict[str, bool]:
            Retrieves the coverage parameters supported by the WCS service for the given version.
        get_coverage(self, filename: Optional[str] = None, **args) -> None:
            Fetches coverages from the WCS service based on specified parameters and saves the response to a file.
    """
    def __init__(self, source: str, name: str, version: Optional[str] = '2.0.1', max_coverages: Optional[int] = 100, timeout: Optional[int] = 90) -> None:
        """
        Initializes a WCSService instance with specified parameters.

        Parameters:
            source (str): The URL of the WCS service endpoint.
            name (str): A name to identify the WCS service.
            version (Optional[str], optional): The WCS protocol version to use (default is '2.0.1').
            max_coverages (Optional[int], optional): Maximum number of coverages to retrieve per request (default is 100).
            timeout (Optional[int], optional): Timeout for WCS requests in seconds (default is 90).
        """
        InspireDownloadService.__init__(self, service='WCS')
        self.source = source.replace('?', '')
        self.name = name
        self.version = version
        self.max_coverages = max_coverages
        self.timeout = timeout
        self.__capabilities = WCSCapabilities(self.service, self.version, self.source)
        self.log(f'WCS {name} service READING STARTED')

    def get_coverage_parameters(self) -> Dict[str, bool]:
        """
        Retrieves the coverage parameters supported by the WCS service for the given version.

        Returns:
            (Dict[str, bool]): A dictionary of coverage parameters and their availability (True/False).
        """
        return WCS_PARAMETERS.get(self.version)

    def get_coverage(self, filename:Optional[str]=None, **args) -> None:
        """
        Fetches coverages from the WCS service based on specified parameters and saves the response to a file.

        Notes:
        - Either both RESX and RESY or both WIDTH and HEIGHT must be provided.
        - The response content is written to the specified file, and the directory structure is created if it does not exist.
        
        Parameters:
            filename (Optional[str]): The path to the file where the response will be saved. 
            **args: Additional parameters for the GetCoverage request. This includes but is not limited to:
                - coverage or coverageID (str): The name of the coverage to retrieve.
                - bbox (str): Bounding box for a subset of the coverage.
                - time (str): Time instants or intervals for a temporal subset.
                - RESX (float): Spatial resolution in the x direction.
                - RESY (float): Spatial resolution in the y direction.
                - width (int): Width of the grid.
                - height (int): Height of the grid.
                - interpolation (str): Spatial interpolation method.
                - format (str): Requested output format of Coverage.
                - exceptions (str): Format in which exceptions are to be reported by the server.
        Raises:
            ValueError: If mandatory parameters are missing or if neither RESX/RESY nor WIDTH/HEIGHT is fully provided.

        """
        parameters = self.get_coverage_parameters()
        
        
        # Check for missing required parameters
        missing = [key for (key, value) in parameters.items() if value.get('required') and not args.get(key) and not key in ['service', 'request', 'version']]
        # If there are missing required parameters (other than the conditional sets), raise an error
        if len(missing) > 0:
            self.log(f'The following mandatory parameters are missing: {missing}', logging.CRITICAL)
            raise ValueError(f'The following mandatory parameters are missing: {missing}')
        
        if self.version == '1.0.0' and not args['coverage'] in self.capabilities.list_coverages():
            # Check for required parameter sets (RESX/RESY or WIDTH/HEIGHT)
            resx_resy_provided = 'RESX' in args and 'RESY' in args
            width_height_provided = 'width' in args and 'height' in args

            # If neither RESX/RESY nor WIDTH/HEIGHT is fully provided, raise an error
            if not resx_resy_provided and not width_height_provided:
                self.log('Either both RESX and RESY, or both WIDTH and HEIGHT, must be provided.', logging.CRITICAL)
                raise ValueError('Either both RESX and RESY, or both WIDTH and HEIGHT, must be provided.')
            coverage = args['coverage']
            self.log(f'The requested coverage {coverage} is not found.', logging.CRITICAL)
            raise ValueError(f'The requested coverage {coverage} is not found.')
        if self.version == '2.0.1' and not args['coverageID'] in self.capabilities.list_coverages():
            coverage = args['coverageID']
            self.log(f'The requested coverage {coverage} is not found.', logging.CRITICAL)
            raise ValueError(f'The requested coverage {coverage} is not found.')
        
        not_valid_params = []
        url = self.source + f'?service=WCS&version={self.version}&request=GetCoverage'
        # Loop through the provided arguments and append them to the URL if valid
        for arg in args:
            if arg in parameters:
                value = args.get(arg)
                if isinstance(value, list):
                    for item in value:
                        url += f'&{arg.upper()}={item}'
                else:
                    url += f'&{arg.upper()}={value}'
            else:
                not_valid_params.append(arg)
        # Notify if there are any invalid parameters
        if len(not_valid_params) > 0:
            self.log(f'The following parameters have been excluded: {not_valid_params}\nValid params for WCS version {self.version} are: {list(parameters.keys())}', logging.WARNING)
        
        # Fetch data from the WCS service
        if filename:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                try:
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)
                    with open(filename, "wb") as file:
                        file.write(response.content)
                except Exception as e:
                    self.log(f'The coverage file could not be downloaded.\n{e}', logging.ERROR)
        
        return gdal.Open(f'WCS:{url}')
    
    @property
    def capabilities(self):
        return self.__capabilities


class AtomService(InspireDownloadService):
    """ 
    Represents an INSPIRE Atom Download Service for fetching geospatial data.

    This class provides functionality for interacting with Atom feeds, recursively extracting links to datasets 
    (such as GML files), and retrieving geospatial features from those datasets.

    Attributes:
        source (str): The URL of the Atom feed.
        name (str): A name for identifying the Atom service instance.

    ## Methods
        is_atom() -> bool: 
            Determines whether the source is an Atom service by checking if the URL ends with '.xml'.
        recurse_links(parent_link: Optional[str] = None, xml: str = None) -> Generator[str, None, None]:
            Recursively extracts and yields dataset links (e.g., GML files) from an Atom feed XML document.
        _get_ogr_feature(gml: str, typeNames: str) -> Generator[ogr.Feature, None, None]:
            Parses GML data and extracts geospatial features as OGR Feature objects based on the specified type names.
        get_feature(typeNames: str, FILES: Optional[str] = None) -> Generator[ogr.Feature, None, None]:
            Fetches geospatial features from the Atom service by processing GML or ZIP files, filtered by the specified type names and optional file filters.
    """
    def __init__(self, source:str, name:str) -> None:
        """
        Initializes the AtomService with the specified source and name.

        Parameters:
            source (str): The URL of the Atom feed.
            name (str): The name of the Atom service.
        """
        super().__init__(service='ATOM')
        self.source = source.replace('?', '')
        self.name = name
        self.log(f'ATOM service {name} READING STARTED')

    def is_atom(self) -> bool:
        """
        Checks if the data source is an Atom service.

        Returns:
            bool: True if the source is an Atom feed, False otherwise.
        """
        return self.source.lower().endswith('.xml')

    def recurse_links(self, parent_link:Optional[str] = None , xml:Optional[str] = None) -> Generator[str, None, None]:
        """
        Recursively extracts and yields dataset links (e.g., GML files) from an Atom feed XML document.

        This method identifies valid links to datasets (such as GML or ZIP files) and handles nested Atom feeds, if present.

        Parameters:
            parent_link (Optional[str]): The URL to the previous page (just for non standarized, should be removed). Defaults to None.
            xml (Optional[str]): ATOM Feed XML. Defaults to None.
        
        Yields:
            str: URLs of the dataset links found in the Atom feed.
        """
        # If it is an HTML file, then recursively request all the GML files contained in it
        html = BeautifulSoup(xml, features="lxml")
        metadata = [link for link in html.findAll('link', href=True) if (link.attrs.get('type') == "application/vnd.iso.19139+xml" or link.attrs.get('type') == "application/xml")]
        links = []
        feeds = html.findAll('feed')
        for feed in feeds:
            [links.extend(entry.findAll('link', href=True)) for entry in feed.findAll('entry')]
        for link in links:
            href = link.attrs.get('href').lower()
            if (link.attrs.get('type') == "application/atom+xml" and href.endswith('.xml')):
                new_xml = utils.request(href)
                if new_xml and new_xml != xml:
                    yield from self.recurse_links(parent_link=href, xml=new_xml)
            elif link != metadata and link not in metadata and link.name == 'link':
                if href.startswith('http') or href.startswith('https'):
                    yield href

    def _get_ogr_feature(self, gml:str, typeNames:str) -> Generator[ogr.Feature, None, None]:
        """
        Parses GML data and extracts features as OGR Feature objects.

        Parameters:
            gml (str): The GML content as a string.
            typeNames (str): A comma-separated list of feature type names to filter the results.

        Yields:
            ogr.Feature: The geospatial features extracted from the GML data that match the specified type names.
        """
        # https://gdal.org/drivers/vector/georss.html
        gdal.FileFromMemBuffer('/vsimem/temp', gml)
        data_source = ogr.Open('/vsimem/temp')
        for index in range(data_source.GetLayerCount()):
            layer = data_source.GetLayerByIndex(index).GetName().split(':')[1] if len(data_source.GetLayerByIndex(index).GetName().split(':')) == 2 else data_source.GetLayerByIndex(index).GetName()
            if layer in typeNames.replace(' ', '').split(','):
                for feature in data_source.GetLayerByName(layer):
                    super().add_errors_to_feature(feature)
                    yield feature

    def get_feature(self, typeNames:str, FILES:Optional[str] = None) -> Generator[ogr.Feature, None, None]:
        """
        Retrieves geospatial features from the Atom service based on the specified type names and optional file filters.

        This method fetches the Atom feed, processes GML or ZIP files, and extracts features from them.

        Parameters:
            typeNames (str): A comma-separated list of type names to fetch features from.
            FILES (Optional[str]): Specific file names to filter datasets by (e.g., filtering GML or ZIP files). Defaults to None.

        Yields:
            ogr.Feature: Geospatial features fetched from the Atom service.

        Raises:
            ValueError: If the provided source is not an Atom feed, or if the format is not recognized.
        """
        response = requests.get(self.source)
        if response.status_code == 200:
            feed = response.content.decode('utf-8')
            if self.is_atom():
                if feed.strip().lower().endswith('</html>') or feed.strip().endswith('</feed>'):
                    for link in self.recurse_links(xml=feed):
                        if link.endswith('.gml'):
                            if not FILES or (FILES and link.split('/')[-1].upper() in FILES.upper().replace(' ','').split(',')):
                                response = requests.get(link)
                                if response.status_code == 200:
                                    gml = response.content.decode('utf-8')
                                    try:
                                        # Convert from UTF-8 to Latin-1
                                        gml = gml.encode('latin-1', 'ignore').decode('latin-1')
                                    except UnicodeEncodeError as e:
                                        self.log(f"Error converting text to Latin-1: {e}", logging.ERROR)
                                    yield from self._get_ogr_feature(gml, typeNames)
                        elif link.endswith('.zip'):
                            if not FILES or (FILES and link.split('/')[-1].upper() in FILES.upper().replace(' ','').split(',')):
                                with ZipFile(io.BytesIO(requests.get(link, timeout=10000).content)) as zip_file:# 10s timeout
                                    for file in zip_file.filelist:
                                        if file.filename.endswith('.gml'):
                                            with zip_file.open(file.filename, 'r') as zipped_gml:
                                                gml = zipped_gml.read().decode('utf-8')
                                                try:
                                                    # Convert from UTF-8 to Latin-1
                                                    gml = gml.encode('latin-1', 'ignore').decode('latin-1')
                                                except UnicodeEncodeError as e:
                                                    self.log(f"Error converting text to Latin-1: {e}", logging.ERROR)
                                                yield from self._get_ogr_feature(gml, typeNames)
                else:
                    self.log('Format not recognized. Valid format is Atom Feed.', logging.CRITICAL)
                    raise ValueError('Format not recognized. Valid format is Atom Feed.')
            else:
                self.log('The provided source is not an ATOM Feed.', logging.CRITICAL)
                raise ValueError('The provided source is not an ATOM Feed.')


class OGCAPIService(InspireDownloadService):
    """ 
    Fetches features and coverages from an OGC API Download Service.

    This class provides functionality to interact with an OGC API service to retrieve geospatial features 
    and coverages. It supports fetching data collections, querying parameters, filtering results, and setting 
    coordinate reference systems (CRS) for specific layers.

    Attributes:
        source (str): The base URL of the OGC API service, with any trailing '?' characters removed.
        name (str): The name of the OGC API service.
        ds (ogr.DataSource): The OGR data source for accessing layers from the OGC API.
        __capabilities (OpenAPIDoc): The OpenAPI documentation instance used to inspect available collections, 
                                     parameters, and queryables.
        
    Methods:
        get_collections() -> List[str]:
            Retrieves a list of all collection names (layers) available in the OGC API service.
        get_layer(collectionId: str) -> ogr.Layer:
            Fetches a specific layer (collection) by its identifier from the OGC API service.
        get_available_parameters() -> Dict[str, str]:
            Retrieves available query parameters from the OGC API service's OpenAPI documentation.
        get_queryable_properties(collectionId: str) -> Dict[str, str]:
            Retrieves the queryable properties for a given collection.
        is_crs_supported(collectionId: str, crs: str) -> bool:
            Checks if a specified Coordinate Reference System (CRS) is supported by a collection.
        set_layer_crs(layer: ogr.Layer, crs: str) -> None:
            Sets the CRS for a given layer.
        build_filter(collectionId: str, **args) -> str:
            Constructs a SQL filter string based on the provided arguments.
        get_feature(collectionId: str, SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]:
            Retrieves features from a specified collection, applying optional filters.
        get_coverage(collectionId: str, filename: Optional[str] = None, **args) -> Optional[Dict]:
            Fetches coverage data from the OGC API service, optionally saving it to a file.
    """
    def __init__(self, source:str, name:str) -> None:
        """
        Initializes the OGCAPIService with a given source URL and service name.
        
        Side Effects:
            Initializes the data source for OGR using the given service URL.
            Logs the start of the OGC API service reading process.

        Parameters:
            source (str): The URL of the OGC API service.
            name (str): A name identifier for the service.
        """
        super().__init__(service='OGCAPI')
        self.source = source.replace('?', '')
        self.name = name
        self.__capabilities = OpenAPIDoc(self.source)
        collection_type = self.capabilities._detect_api_type()
        if collection_type == 'items':
            super()._set_ds(ogr.Open(f'OAPIF:{self.source}'))
        else:
            super()._set_ds(ogr.Open(f'OGCAPI:{self.source}'))
            
        self.log(f'OGC API service {name} READING STARTED')
    
    def get_layer(self, collectionId:str) -> ogr.Layer:
        """
        Fetches a specific layer (collection) by its identifier from the OGC API service.

        Parameters:
            collectionId (str): The identifier of the collection to fetch.

        Returns:
            ogr.Layer: The requested layer object. If the layer does not exist, returns None.
        """
        return self.ds.GetLayerByName(collectionId)
    
    def set_layer_crs(self, layer:ogr.Layer, crs:str) -> None:
        """
        Sets the CRS for a given layer.
        
        Side Effects:
            Modifies the active spatial reference system (SRS) of the specified layer if the CRS is valid.

        Parameters:
            layer (ogr.Layer): The OGR layer to set the CRS for.
            crs (str): The CRS to set, provided in a format recognized by OGR.
        """
        dest_srs = ogr.osr.SpatialReference()
        if dest_srs.SetFromUserInput(crs) == 0:
            layer.SetActiveSRS(0, dest_srs)
            
    def get_url_params(self, collectionId: str, **args) -> Optional[str]:
        """
        Constructs a query string from the available parameters for a given collection.

        Parameters:
            collectionId (str): The identifier of the collection.
            **args: Arbitrary keyword arguments representing the parameters.

        Returns:
            Optional[str]: A query string of the form "param1=value1&param2=value2", or None if no parameters match.
        """
        params = []
        
        collection_type = self.capabilities._detect_api_type()
        parameters = self.capabilities.get_operation_parameters(f'/collections/{collectionId}/{collection_type}')
        if parameters:
            for arg in args:
                key = arg.replace('_', '-')
                value = args.get(arg)
                if key in parameters.keys():
                    params.append(f"{key}={value}")
        
        return '&'.join(params) if params else None
    
    def get_url_queryables(self, collectionId: str, **args) -> Optional[str]:
        """
        Constructs a query string based on the queryable properties of a collection.

        Parameters:
            collectionId (str): The identifier of the collection.
            **args: Arbitrary keyword arguments representing the queryable parameters.

        Returns:
            Optional[str]: A query string of the form "key=value" based on queryables, or None if no queryables match.
        """
        params = []
        
        collection_type = self.capabilities._detect_api_type()
        queryables = self.capabilities.get_operation_queryables(operation=f'/collections/{collectionId}/{collection_type}')
        if queryables:
            for arg in args:
                key = arg if arg in queryables.keys() else arg.replace('_', '-')
                value = args.get(arg)
                if key in queryables.keys() or arg in queryables.keys():
                    key = queryables.get(key).get('x-ogc-role') or key
                    data_type = queryables.get(key).get('type') or queryables.get(key).get('type')
                    where =  f'{key}={value}'
                    params.append(where)
        
        return '&'.join(params) if params else None
    
    def get_full_url(self, collectionId: str, **args) -> str:
        """
        Constructs the full URL for retrieving a collection from the OGC API service, including any query parameters.

        Parameters:
            collectionId (str): The identifier of the collection.
            **args: Arbitrary keyword arguments representing the query parameters.

        Returns:
            str: The full URL including query parameters.
        """
        collection_type = self.capabilities._detect_api_type()
        params = [self.get_url_params(collectionId=collectionId, **args), self.get_url_queryables(collectionId=collectionId, **args)]
        params = '&'.join([param for param in params if param is not None])
        return self.source.rstrip('/') + f'/collections/{collectionId}/{collection_type}?' + params.replace(' ', '%20')
    
    def get_map(self, collectionId: str, filename: Optional[str] = None, **args) -> Optional[gdal.Dataset]:
        """
        Retrieves a map (coverage) from the OGC API service.

        Parameters:
            collectionId (str): The identifier of the collection to retrieve the map from.
            filename (Optional[str]): If provided, saves the map to this file path.
            **args: Arbitrary keyword arguments representing the query parameters.

        Returns:
            Optional[gdal.Dataset]: The dataset if successfully retrieved, or None if no coverage is available.
        """
        collection_type = self.capabilities._detect_api_type()
        if collection_type == 'map':
            new_url = self.get_full_url(collectionId=collectionId, **args)
            # Fetch data from the OGC API Coverages service
            if filename:
                response = requests.get(new_url, timeout=30)
                if response.status_code == 200:
                    try:
                        Path(filename).parent.mkdir(parents=True, exist_ok=True)
                        with open(filename, "wb") as file:
                            file.write(response.content)
                    except Exception as e:
                        self.log(f'The coverage file could not be downloaded.\n{e}', logging.ERROR)
            
            return gdal.Open(new_url)
        
        else:
            self.log('The current OGC API Service has no coverages.', logging.WARNING)
        
        return None
        
    def get_feature(self, collectionId:str, SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]:
        """
        Retrieves features from a specified collection, applying optional filters.

        This method fetches features from the specified collection, optionally filtering them using a SQL predicate or other parameters.

        Parameters:
            collectionId (str): The identifier of the collection from which to fetch features.
            SQL_PREDICATE (Optional[str]): An optional SQL predicate string to filter features.
            **args: Arbitrary keyword arguments representing additional filter parameters.

        Yields:
            ogr.Feature: Features from the collection that match the given filters.

        Raises:
            ValueError: If a required parameter is missing or a provided CRS is unsupported.
        """
        # https://gdal.org/drivers/vector/oapif.html
        # All the parameters must be passed as a SQL query
        # Parameters are case-sensitive and must be kebab-case (parameter-name)
        if self.capabilities._detect_api_type() == 'items':
            new_url = self.get_full_url(collectionId=collectionId, **args)
            super()._set_ds(ogr.Open(new_url))
            if self.ds is not None:
                layer = self.ds.GetLayer()
                if layer:
                    if 'crs' in [arg.lower() for arg in args]:
                        crs = args.get('crs') or args.get('CRS')
                        if self.capabilities.is_output_crs_supported(collectionId=collectionId, crs=crs):
                            self.set_layer_crs(layer=layer, crs=crs)
                        if SQL_PREDICATE:
                            yield from self._SQL_filter_on_ds(data_source=self.ds, index=0, SQL_PREDICATE=SQL_PREDICATE)
                        else:
                            self.log(f'Features found: {layer.GetFeatureCount()}')
                            for feature in layer:
                                super().add_errors_to_feature(feature)
                                yield feature
        else:
            self.log('The current OGC API Service has no features.', logging.WARNING)
                
    def get_coverage(self, collectionId: str, filename: Optional[str] = None, **args) -> Optional[Dict]:
        """
        Fetches coverage data from the OGC API service.

        This method retrieves coverage data from the specified collection. If a filename is provided, the coverage
        data will be saved to the specified file path. The response can be returned in either JSON or text format,
        depending on the parameters passed.

        Parameters:
            collectionId (str): The identifier of the collection from which to fetch coverage.
            filename (Optional[str]): If provided, saves the coverage to this file path.
            **args: Arbitrary keyword arguments representing additional parameters.

        Returns:
            Optional[Dict]: The coverage data in JSON format if the request is successful, otherwise None.
        """
        collection_type =  self.capabilities._detect_api_type()
        if collection_type == 'coverage':
            new_url = self.get_full_url(collectionId=collectionId, **args)
            # Fetch data from the OGC API Coverages service
            response = requests.get(new_url, timeout=30)
            if response.status_code == 200:
                try:
                    if filename:
                        Path(filename).parent.mkdir(parents=True, exist_ok=True)
                        with open(filename, "wb") as file:
                            file.write(response.content)
                    if not 'f' in args or ('f' in args and args.get('f') == 'json'):
                        return response.json()
                    else:
                        return response.text
                except Exception as e:
                    self.log(f'The coverage file could not be downloaded.\n{e}', logging.ERROR)
        else:
            self.log('The current OGC API Service has no coverages.', logging.WARNING)
        
        return None
            
    @property
    def capabilities(self):
        return self.__capabilities