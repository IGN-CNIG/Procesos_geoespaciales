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

Email: atencion.cnig@cnig.es

"""
import io
import logging
import requests
from typing import Tuple, List, Dict, Optional, Union, Any

from openapi_spec_validator import validate_spec
import xml.etree.ElementTree as ET


class StoredQuery:
    """
    Represents a stored query in a geospatial service.

    A stored query is a pre-defined query that can be executed to retrieve data from a geospatial service.
    This class encapsulates the details of a stored query, including its parameters and metadata.

    Attributes:
        identifier (str): The unique identifier for the stored query.
        title (str): The title of the stored query.
        abstract (str): A brief description or abstract of the stored query.
        parameters (Dict[str, Dict[str, str]]): A dictionary of parameters for the stored query,
            where the key is the parameter name and the value is a dictionary containing details
            about the parameter, such as 'description' and 'type'.

    ## Methods
        __repr__() -> str:
            Returns a string representation of the StoredQuery instance.

        has_parameter(param_name: str) -> bool:
            Checks if a parameter exists in the stored query.
    """
    
    def __init__(self, identifier: str, title: str, abstract: str, parameters: Dict[str, Dict[str, str]]):
        """
        Initializes a StoredQuery instance with the given details.

        Parameters:
            identifier (str): The unique identifier for the stored query.
            title (str): The title of the stored query.
            abstract (str): A brief description or abstract of the stored query.
            parameters (Dict[str, Dict[str, str]]): A dictionary of parameters for the stored query,
                where the key is the parameter name and the value is a dictionary containing details
                about the parameter, such as 'description' and 'type'.
        """
        self.identifier = identifier
        self.title = title
        self.abstract = abstract
        self.parameters = parameters

    def __repr__(self) -> str:
        """
        Returns a string representation of the StoredQuery instance.

        Returns:
            str: A string representation of the StoredQuery instance.
        """
        return (f"StoredQuery(identifier={self.identifier}, title={self.title}, "
                f"abstract={self.abstract}, parameters={self.parameters})")
    
    def has_parameter(self, param_name: str) -> bool:
        """
        Checks if a parameter exists in the stored query.

        Parameters:
            param_name (str): The name of the parameter to check.

        Returns:
            bool: True if the parameter exists, False otherwise.
        """
        return param_name in self.parameters
    
    
class Coverage:
    """
    Represents a coverage in an INSPIRE Web Coverage Service (WCS).

    This class encapsulates details about a coverage offered by an INSPIRE-compliant WCS service. 
    A coverage represents a type of geospatial data that is typically used in environmental monitoring, 
    modeling, and other applications where spatial data is crucial.

    Attributes:
        name (str): The unique name of the coverage.
        label (str): A human-readable label or title for the coverage.
        description (str): A detailed description of the coverage, including its purpose, content, and any relevant metadata.
        domainsets (str): Information about the domain set of the coverage, defining the spatial and temporal extent of the data.
        rangesets (str): Information about the range set of the coverage, describing the data values or measurements represented.
        crs (str): The coordinate reference systems supported by the coverage, indicating how spatial data is referenced.
        formats (str): The data formats supported by the coverage, specifying the formats in which the coverage data can be accessed or downloaded.
        interpolations (str): The interpolation methods supported by the coverage, detailing how data values are estimated between known points.

    ## Methods
        __repr__() -> str:
            Returns a string representation of the Coverage instance, providing a summary of its attributes.
    """
    
    def __init__(self, name: str, label:str, description:str, domainset:str,
                rangeset:str, supported_crs:str, supported_formats:str, supported_interpolations:str):
        self.name = name
        self.label = label
        self.description = description
        self.domainsets = domainset
        self.rangesets = rangeset
        self.crs = supported_crs
        self.formats = supported_formats
        self.interpolations = supported_interpolations
        
    def __repr__(self) -> str:
        """
        Returns a string representation of the Coverage instance.

        The representation includes all the attributes of the Coverage instance
        to provide a clear and concise summary of its state.

        Returns:
            str: A string representation of the Coverage instance.
        """
        return (f"Coverage(name={self.name!r}, label={self.label!r}, description={self.description!r}, "
                f"domainsets={self.domainsets!r}, rangesets={self.rangesets!r}, crs={self.crs!r}, "
                f"formats={self.formats!r}, interpolations={self.interpolations!r})")
        

class Capabilities:
    """
    The Capabilities class is responsible for interacting with and extracting information from 
    geospatial service capabilities documents (WFS, WCS). It provides methods to fetch, parse, 
    and retrieve relevant metadata such as service type, CRS, and bounding boxes from the capabilities documents.

    Attributes:
        logger (logging.Logger): A logger instance for logging messages.
        url (str): The base URL of the geospatial service.
        service_type (str): The type of service (WFS, WCS, etc.).
        version (str): The version of the service capabilities document.
        tree (Optional[ElementTree]): The parsed XML tree of the capabilities document.
        root (Optional[Element]): The root element of the XML tree.
        namespaces (Dict[str, str]): A dictionary of XML namespaces extracted from the capabilities document.
        
    ## Methods
        log(message: str, level: Optional[str] = logging.INFO) -> None:
            Logs a message with the specified logging level (INFO by default). If no logger is available, it prints the message to the console.
        _fetch_capabilities() -> None:
            Fetches the capabilities document from the specified service URL and parses it into an XML tree. Raises an exception if fetching fails.
        _extract_namespaces(xml_content: io.BytesIO) -> Dict[str, str]:
            Extracts and returns namespaces from the given XML content. This method is a static method.
        get_service_type() -> Optional[str]:
            Returns the type of the service (e.g., WFS or WCS). This method is tied to the instance as it relies on instance attributes.
        get_crs_identifier(crs_uri: str) -> Optional[str]:
            Class method to fetch and parse a CRS document from the given URI, returning the CRS identifier in 'codeSpace:identifier' format if found.
        _read_envelope(envelope: ET.Element) -> Optional[Tuple[List[float], Optional[str]]]:
            Reads an envelope (bounding box) element from the capabilities document to extract its bounding coordinates and spatial reference system (SRS).
    """
    logger:logging.Logger = logging.getLogger(__name__)
    
    def __init__(self, service:str, version:str, url: str) -> None:
        self.url = url.replace('?', '')
        self.service_type = service
        self.version = version
        self.tree = None
        self.root = None
        self.namespaces = {}  # To hold dynamically fetched namespaces
        self._fetch_capabilities()
        
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

    def _fetch_capabilities(self) -> None:
        """
        Fetches the capabilities document, parses it, and extracts namespaces.
        
        Raises:
            Exception: If the capabilities document cannot be fetched.
        """
        self.log(f"Fetching capabilities from {self.url}", logging.INFO)
        try:
            response = requests.get(self.url + f'?service={self.service_type}&version={self.version}&request=GetCapabilities', timeout=30)
            if response.status_code == 200:
                self.tree = ET.ElementTree(ET.fromstring(response.content))
                self.root = self.tree.getroot()
                xml_content = response.content
                self.namespaces = self._extract_namespaces(io.BytesIO(xml_content))
            else:
                self.log(f"Failed to fetch capabilities: {response.status_code}", logging.CRITICAL)
                raise Exception(f"Failed to fetch capabilities: {response.status_code}")
        except Exception as e:
            self.log(f"Error fetching capabilities: {str(e)}", logging.CRITICAL)
            raise
    
    @staticmethod
    def _extract_namespaces(xml_content: io.BytesIO) -> Dict[str, str]:
        """
        Extracts namespaces from the XML content.

        Parameters:
            xml_content (io.BytesIO): The XML content to extract namespaces from.

        Returns:
            Dict[str, str]: A dictionary of namespace prefixes and their URIs.
        """
        Capabilities.log("Extracting namespaces from capabilities document", logging.DEBUG)
        namespaces = {}
        events = "start", "start-ns"
        for event, elem in ET.iterparse(xml_content, events):
            if event == "start-ns":
                prefix, uri = elem
                namespaces[prefix] = uri
        
        Capabilities.log(f"Namespaces extracted: {namespaces}", logging.DEBUG)
        return namespaces
    
    def get_service_type(self) -> Optional[str]:
        """
        Determines the type of service (WFS or WCS) from the capabilities document.

        Returns:
            Optional[str]: The service type ('WFS' or 'WCS') or None if the type cannot be determined.
        """
        return self.service_type
    
    @classmethod
    def get_crs_identifier(cls, crs_uri: str) -> Optional[str]:
        """
        Fetches and parses the CRS document from the given URI to extract CRS information.

        Parameters:
            crs_uri (str): The URI of the CRS document to fetch.

        Returns:
            Optional[str]: A string with the CRS identifier in the format 'codeSpace:identifier' if found, otherwise None.
        """
        cls.log(f"Fetching CRS identifier from URI: {crs_uri}", logging.INFO)
        # Fetch the CRS document
        try:
            response = requests.get(crs_uri, timeout=30)
            if response.status_code == 200:
                # Parse the CRS document
                crs_tree = ET.ElementTree(ET.fromstring(response.content))
                crs_root = crs_tree.getroot()
                crs_namespaces = cls._extract_namespaces(cls, io.BytesIO(response.content))
                
                    # Search for CRS definitions in the capabilities document
                crs_elements = crs_root.findall('gml:identifier', namespaces=crs_namespaces)
                if crs_elements:
                    crs_elem = crs_elements[0]
                    code_space = crs_elem.get('codeSpace', 'UnknownCodeSpace')
                    identifier = crs_elem.text
                    return f"{code_space}:{identifier}"
            cls.log(f"No CRS identifier found at {crs_uri}", logging.WARNING)
        except Exception as e:
            cls.log(f"Error fetching CRS identifier: {str(e)}", logging.ERROR)
        
        return None
    
    def _read_envelope(self, envelope:ET.Element) -> Optional[Tuple[List[float], Optional[str]]]:
        """
        Parses an envelope element to extract its bounding coordinates and spatial reference system (SRS) name.

        This method processes an XML element representing an envelope, which is commonly used to describe
        the bounding box of a spatial feature in geospatial data. It retrieves the lower-left and upper-right
        corner coordinates of the envelope and the SRS name if available.

        Parameters:
            envelope (ET.Element): The XML element representing the envelope, expected to contain GML elements
                with positional coordinates and an optional SRS name.

        Returns:
            (Optional[Tuple[List[float], Optional[str]]]): If the envelope is not valid or does not contain exactly two position elements, returns None.
            The Tuple contains:
            - A list of four float values representing the coordinates of the lower-left and upper-right
                corners of the envelope ([ll_x, ll_y, ur_x, ur_y]).
            - An optional string representing the SRS name of the envelope, or None if not specified.
            
        """
        self.log(f"Reading envelope from XML element", logging.DEBUG)
        if envelope is not None:
            srs_name = envelope.attrib.get('srsName', None)
            axis_names = envelope.attrib.get('axisLabels', None)
            if axis_names is not None:
                axis_names = axis_names.split()
            # version 1.0.0
            pos_elements = envelope.findall('gml:pos', namespaces=self.namespaces)
            if len(pos_elements) == 2:
                ll_corner = [float(coord) for coord in pos_elements[0].text.split()]
                ur_corner = [float(coord) for coord in pos_elements[1].text.split()]
                self.log(f"Envelope coordinates found: {ll_corner}, {ur_corner}, SRS: {srs_name}", logging.INFO)
                return ([ll_corner[0], ll_corner[1], ur_corner[0], ur_corner[1]], srs_name)
            # version 2.0.1
            ll_corner = envelope.find('gml:lowerCorner', namespaces=self.namespaces)
            ur_corner = envelope.find('gml:upperCorner', namespaces=self.namespaces)
            if ll_corner is not None and ur_corner is not None:
                ll_corner = [float(coord) for coord in ll_corner.text.split()]
                ur_corner = [float(coord) for coord in ur_corner.text.split()]
                self.log(f"Envelope coordinates found: {ll_corner}, {ur_corner}, SRS: {srs_name}", logging.INFO)
                return ([ll_corner[0], ll_corner[1], ur_corner[0], ur_corner[1]], srs_name, axis_names)
        
        self.log("Invalid or incomplete envelope element", logging.WARNING)
        return (None, None, None)


class WFSCapabilities(Capabilities):
    """
    A class to represent and interact with a Web Feature Service (WFS) capabilities document.

    This class extends the `Capabilities` base class to provide specific functionalities for handling
    WFS capabilities, including querying stored queries, feature types, and service constraints. 

    Attributes:
        stored_queries (Optional[Dict[str, StoredQuery]]): A dictionary of stored queries available in the WFS service,
            where the key is the title of the stored query and the value is an instance of `StoredQuery`.

    ## Methods
        _get_stored_queries() -> Optional[Dict[str, StoredQuery]]:
            Retrieves and parses stored queries available in the WFS service.
        get_service_info() -> Optional[Dict[str, str]]:
            Retrieves general information about the WFS service, including title, abstract, and version.
        get_operations() -> List[str]:
            Retrieves the available operations from the capabilities document.
        get_parameters() -> Dict[str, Dict[str, Union[str, List[str]]]]:
            Queries and extracts parameters defined in the capabilities document, including allowed values and default values.
        get_constraints() -> Dict[str, Dict[str, Union[str, List[str]]]]:
            Retrieves service constraints from the capabilities document, including allowed values and default values.
        query_constraint(constraint_name: str) -> Optional[Dict[str, Union[str, List[str]]]]:
            Queries details of a specific constraint by name, including allowed values and default value if available.
        get_feature_types() -> List[Dict[str, str]]:
            Retrieves all available feature types in the WFS service, including their names and titles.
        query_feature_type(feature_name: str) -> Optional[Dict[str, Union[str, List[str]]]]:
            Queries details for a specific feature type, including CRS information and output formats.
        list_stored_queries() -> List[Dict[str, str]]:
            Lists stored queries available in the WFS capabilities document with their IDs and titles.
    """
    def __init__(self, service:str, version:str, url: str):
        """
        Initializes the WFSCapabilities instance and fetches the WFS capabilities document.

        Parameters:
            url (str): URL to the WFS GetCapabilities document.
        """
        super().__init__(service, version, url)
        self.stored_queries = self._get_stored_queries()
        
    def _get_stored_queries(self) -> Optional[Dict[str, StoredQuery]]:
        """
        Retrieves and parses stored queries available in the WFS service.

        Checks if the WFS service supports stored queries, then requests and processes them,
        storing them in the `stored_queries` attribute.

        Returns:
            (Optional[Dict[str, StoredQuery]]): A dictionary of stored queries if available, otherwise None.
        """
        queries = {}
        
        if 'ListStoredQueries' in self.get_operations():
            list_stored_queries_url = f"{self.url}?service=WFS&version=2.0.0&request=ListStoredQueries"
            response = requests.get(list_stored_queries_url,timeout=30)
            
            if response.status_code == 200:
                list_stored_queries_xml = response.content
                list_stored_queries_root = ET.fromstring(list_stored_queries_xml)
                
                stored_queries_elements = list_stored_queries_root.findall('.//wfs:StoredQuery', namespaces=self.namespaces)
                
                for stored_query_elem in stored_queries_elements:
                    identifier = stored_query_elem.get('id')
                    
                    describe_stored_queries_url = f"{self.url}?service=WFS&version=2.0.0&request=DescribeStoredQueries&storedQuery_ID={identifier}"
                    response = requests.get(describe_stored_queries_url, timeout=30)
                    
                    if response.status_code == 200:
                        describe_stored_queries_xml = response.content
                        describe_stored_queries_root = ET.fromstring(describe_stored_queries_xml)
                        
                        description_elem = describe_stored_queries_root.find('.//wfs:StoredQueryDescription', namespaces=self.namespaces)
                        
                        if description_elem is not None:
                            title_elem = description_elem.find('wfs:Title', namespaces=self.namespaces)
                            abstract_elem = description_elem.find('wfs:Abstract', namespaces=self.namespaces)
                            
                            # Handle multiple language abstracts
                            abstract_texts = {abstract_elem.get('{http://www.w3.org/XML/1998/namespace}lang'): abstract_elem.text} if abstract_elem is not None else {}
                            for lang_elem in description_elem.findall('wfs:Abstract', namespaces=self.namespaces):
                                lang = lang_elem.get('{http://www.w3.org/XML/1998/namespace}lang')
                                if lang:
                                    abstract_texts[lang] = lang_elem.text
                            
                            # Convert the abstract to a single string (choose a default language or concatenation)
                            abstract = abstract_texts.get('en', 'No Abstract')  # Default to English, if available
                            
                            parameters = {}
                            for param_elem in description_elem.findall('wfs:Parameter', namespaces=self.namespaces):
                                param_name = param_elem.get('name')
                                param_description = param_elem.find('wfs:Abstract', namespaces=self.namespaces)
                                param_type = param_elem.get('type')
                                param_type = param_type.split(':')[1] if len(param_type.split(':')) == 2 else param_type
                                parameters[param_name] = {
                                    'description': param_description.text if param_description is not None else 'No Description',
                                    'type': param_type
                                }
                            
                            title = title_elem.text if title_elem is not None else 'No Title'
                            query_description = {
                                'identifier': identifier,
                                'title': title,
                                'abstract': abstract,
                                'parameters': parameters
                            }
                            queries[title] = StoredQuery(**query_description)
        return queries
        
    def get_service_info(self) -> Optional[Dict[str, str]]:
        """
        Retrieves general information about the service.

        Returns:
            (Optional[Dict[str, str]]): A dictionary containing 'title', 'abstract', and 'version' of the service, or None if not found.
        """
        service_identification = self.root.find('ows:ServiceIdentification', namespaces=self.namespaces)
        if service_identification is not None:
            service_title = service_identification.find('ows:Title', namespaces=self.namespaces).text
            service_abstract = service_identification.find('ows:Abstract', namespaces=self.namespaces).text
            service_version = service_identification.find('ows:ServiceTypeVersion', namespaces=self.namespaces).text
            return {
                'title': service_title,
                'abstract': service_abstract,
                'version': service_version
            }
        return None
    
    def get_operations(self) -> List[str]:
        """
        Retrieves available operations from the capabilities document.

        Returns:
            List[str]: A list of operation names available in the service.
        """
        operations = self.root.findall('.//ows:OperationsMetadata/ows:Operation', namespaces=self.namespaces)
        return [op.get('name') for op in operations]
    
    def get_parameters(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """
        Queries the parameters defined in the capabilities document.

        This method extracts parameters and their allowed values from the capabilities XML.

        Returns:
            (Dict[str, Dict[str, Union[str, List[str]]]]): A dictionary where keys are parameter names and values are dictionaries containing
                'allowed_values' and optionally 'default_value'.
        """
        parameters = {}
        params_elements = self.root.findall('.//ows:Parameter', namespaces=self.namespaces)

        for param in params_elements:
            name = param.get('name')
            allowed_values_elem = param.find('ows:AllowedValues', namespaces=self.namespaces)
            if allowed_values_elem is not None:
                allowed_values = [value_elem.text for value_elem in allowed_values_elem.findall('ows:Value', namespaces=self.namespaces)]
            else:
                allowed_values = []

            param_info = {'allowed_values': allowed_values}

            default_value = param.find('ows:DefaultValue', namespaces=self.namespaces)

            if default_value is not None:
                param_info['default_value'] = default_value.text

            parameters[name] = param_info

        return parameters
        
    def get_constraints(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """
        Retrieves service constraints, including allowed values and default values.

        Returns:
            (Dict[str, Dict[str, Union[str, List[str]]]]): A dictionary of constraints where each key is a constraint name
                and the value is another dictionary with 'allowed_values' and optionally 'default_value'.
        """
        constraints = {}
        constraint_elements = self.root.findall('.//{http://www.opengis.net/ows/1.1}Constraint', namespaces=self.namespaces)
        
        for constraint in constraint_elements:
            name = constraint.get('name')

            # Check for allowed values
            allowed_values = [value.text for value in constraint.findall('ows:AllowedValues/ows:Value', namespaces=self.namespaces)]

            # Check for default value
            default_value = constraint.find('ows:DefaultValue', namespaces=self.namespaces)

            constraint_info = {'allowed_values': allowed_values}
            if default_value is not None:
                constraint_info['default_value'] = default_value.text

            constraints[name] = constraint_info

        return constraints

    def query_constraint(self, constraint_name: str) -> Optional[Dict[str, Union[str, List[str]]]]:
        """
        Queries details of a specific constraint, including allowed values and default value, if available.

        Parameters:
            constraint_name (str): The name of the constraint to query.

        Returns:
            (Optional[Dict[str, Union[str, List[str]]]]): A dictionary containing 'name', 'allowed_values', and 'default_value' (if present), or None if the constraint is not found.
        """
        # Use the get_constraints method to get all constraints
        all_constraints = self.get_constraints()

        # Search for the specific constraint by name
        if all_constraints.get(constraint_name):
            return all_constraints[constraint_name]

        # Return None if the constraint is not found
        return None

    def get_feature_types(self) -> List[Dict[str, str]]:
        """
        Retrieves all available feature types in the WFS service.

        Returns:
            (List[Dict[str, str]]): A list of dictionaries, each containing 'name' and 'title' of a feature type.
        """
        feature_types = self.root.findall('.//wfs:FeatureType', namespaces=self.namespaces)
        features = []
        for feature in feature_types:
            title = feature.find('wfs:Title', namespaces=self.namespaces).text
            name = feature.find('wfs:Name', namespaces=self.namespaces).text
            features.append({'name': name, 'title': title})
        return features

    def query_feature_type(self, feature_name: str) -> Optional[Dict[str, Union[str, List[str]]]]:
        """
        Query details for a specific feature type, including CRS information and output formats.

        Parameters:
            feature_name (str): The name of the feature type to query.

        Returns:
            (Optional[Dict[str, Union[str, List[str]]]]): A dictionary with details about the feature type, or None if not found.
        """
        feature_types = self.root.findall('.//wfs:FeatureType', namespaces=self.namespaces)
        for feature in feature_types:
            name = feature.find('wfs:Name', namespaces=self.namespaces).text
            if name == feature_name:
                title = feature.find('wfs:Title', namespaces=self.namespaces).text
                
                # Get the default CRS
                default_crs = feature.find('wfs:DefaultCRS', namespaces=self.namespaces).text
                
                # Get any additional CRSs
                other_crs = [crs.text for crs in feature.findall('wfs:OtherCRS', namespaces=self.namespaces)]
                
                output_formats = [f.text for f in feature.findall('wfs:OutputFormats/wfs:Format', namespaces=self.namespaces)]
                
                return {
                    'name': name,
                    'title': title,
                    'default_crs': default_crs,
                    'available_crs': other_crs,
                    'output_formats': output_formats
                }
        return None
    
    def list_stored_queries(self) -> List[Dict[str, str]]:
        """
        Lists stored queries available in the WFS capabilities document.

        Returns:
            (List[Dict[str, str]]): A list of dictionaries where each dictionary represents a stored query with 'id' and 'title'.
        """
        stored_queries = self.root.findall('.//wfs:StoredQuery', namespaces=self.namespaces)
        query_list = []
        for query in stored_queries:
            query_id = query.get('id')
            query_title = query.find('wfs:Title', namespaces=self.namespaces)
            query_list.append({
                'id': query_id,
                'title': query_title.text if query_title is not None else 'No Title'
            })

        return query_list


class WCSCapabilities(Capabilities):
    """
    A class to handle WCS (Web Coverage Service) Capabilities.

    This class retrieves and processes the capabilities document of a WCS service, providing methods to 
    list coverages, describe specific coverages, and retrieve service-level information.

    Attributes:
        version (str): The WCS version being used.
        url (str): The URL to the WCS service capabilities document.
        root (ET.Element): The root element of the parsed XML capabilities document.
        namespaces (Dict[str, str]): A dictionary of XML namespaces used for parsing.
        coverages (Dict[str, Coverage]): A dictionary mapping coverage names to `Coverage` objects.

    ## Methods
        _get_coverages() -> List[Dict[str, Coverage]]:
            Internal method to parse and retrieve all coverages from the WCS capabilities document and create `Coverage` objects.
        get_service_info() -> Optional[Dict[str, str]]:
            Retrieves general information about the WCS service, including title, label, and description.
        get_operations() -> List[str]:
            Retrieves a list of operations that the WCS service supports.
        get_supported_formats() -> List[str]:
            Retrieves the list of supported formats for the WCS service.
        get_supported_crs(self) -> List[str]:
            Retrieves the list of supported Coordinate Reference Systems (CRS) for the WCS service.
        list_coverages() -> Dict[str, Dict[str, Any]]:
            Lists coverages available in the WCS capabilities document, returning a dictionary with coverage
            names as keys and coverage metadata (label, description, bounding box, and SRS) as values.
        describe_coverage(self, coverageID: str) -> Optional[Coverage]:
            Retrieves detailed information about a specific coverage.
    """
    def __init__(self, service:str, version:str, url: str):
        """
        Initializes the WCSCapabilities instance and fetches the WCS capabilities document.

        Parameters:
            version (str): The WCS version.
            url (str): URL to the WCS GetCapabilities document.
        """
        super().__init__(service, version, url)
        self.coverages = self._get_coverages()
    
    def _get_coverages(self):
        """
        Retrieves all the coverages from the WCS capabilities document.

        Returns:
            (List[Dict[str, Coverage]]): A Coverage object with detailed information about the coverage, or None if the coverage is not found.
        """
        if self.version == '1.0.0':
            return self._get_coverages_v1()
        elif self.version == '2.0.1' or self.version is None:
            return self._get_coverages_v2()

    def _get_coverages_v1(self) -> List[Dict[str, Coverage]]:
        coverages = {}
        coverage_elements = self.root.findall('.//CoverageOfferingBrief', namespaces=self.namespaces)
        for coverage in coverage_elements:
            name = coverage.find('name', namespaces=self.namespaces).text
            label = coverage.find('label', namespaces=self.namespaces).text
            description = coverage.find('description', namespaces=self.namespaces).text
            # Find the lonLatEnvelope element
            lon_lat_envelope = coverage.find('lonLatEnvelope', namespaces=self.namespaces)
            bbox, srs_name = self._read_envelope(lon_lat_envelope)

            response = requests.get(self.url + f'?service=WCS&version={self.version}&request=DescribeCoverage&coverage={name}', timeout=30)
            if response.status_code == 200:
                coverage_description_xml = response.content
                coverage_description_root = ET.fromstring(coverage_description_xml)
                coverage_namespaces = self._extract_namespaces(io.BytesIO(response.content))
                
                coverage_description_elements = coverage_description_root.findall('.//CoverageOffering', namespaces=coverage_namespaces)
                for coverage_description_element in coverage_description_elements:
                    
                    spatial_domain = {'Envelopes': [], 'RectifiedGrids': []}
                    domain_sets = coverage_description_element.findall('.//domainSet', namespaces=coverage_namespaces)
                    for domain_set in domain_sets:
                        domain = domain_set.find('spatialDomain', namespaces=coverage_namespaces)
                        
                        envelopes = domain.findall('gml:Envelope', namespaces=coverage_namespaces)
                        for envelope in envelopes:
                            bbox, srs_name = self._read_envelope(envelope)
                            spatial_domain['Envelopes'].append({'bbox':bbox, 'srsName':srs_name})
                        
                        rectified_grids = domain.findall('gml:RectifiedGrid', namespaces=coverage_namespaces)
                        for grid in rectified_grids:
                            grid_limits = grid.find('.//gml:GridEnvelope', namespaces=coverage_namespaces)
                            low = None
                            high = None
                            if grid_limits is not None:
                                low = [int(coord) for coord in grid_limits.findtext('.//gml:low', namespaces=coverage_namespaces).split()]
                                high = [int(coord) for coord in grid_limits.findtext('.//gml:high', namespaces=coverage_namespaces).split()]
                            axis_names = [axis_name.text for axis_name in grid.findall('gml:axisName', namespaces=coverage_namespaces)]
                            origin = grid.find('.//gml:origin/gml:pos', namespaces=coverage_namespaces)
                            if origin is not None:
                                origin = [float(coord) for coord in origin.text.split()]
                            offset_vectors = []
                            for offset in grid.findall('gml:offsetVector', namespaces=coverage_namespaces):
                                    offset_vectors.append([float(coord) for coord in offset.text.split()])
                            spatial_domain['RectifiedGrids'].append(
                                {'rectifiedGrid':
                                    {'limits':
                                        {'low': low, 'high': high}
                                    },
                                    'axisNames': axis_names,
                                    'origin': origin,
                                    'offsetVectors': offset_vectors
                                }
                            )
                    
                    range_sets = []
                    rangesets = coverage_description_element.findall('.//RangeSet', namespaces=coverage_namespaces)
                    for rangeset in rangesets:
                        rs_name = rangeset.find('name', namespaces=coverage_namespaces).text
                        rs_label = rangeset.find('label', namespaces=coverage_namespaces).text
                        range_sets.append({'name':rs_name, 'label':rs_label})
                        
                    crs_info = {}
                    request_response_crss = coverage_description_element.findall('.//requestResponseCRSs', namespaces=coverage_namespaces)
                    crs_info['native'] = coverage_description_element.find('.//nativeCRSs', namespaces=coverage_namespaces).text
                    crs_info['supported'] = [crs.text for crs in request_response_crss]
                    
                    formats = {}
                    supported_formats = coverage_description_element.find('.//supportedFormats', namespaces=coverage_namespaces)
                    formats['native'] = supported_formats.attrib.get('nativeFormat', None)
                    formats['supported'] = [fmt.text for fmt in supported_formats.findall('formats', namespaces=coverage_namespaces)]
                        
                    interpolations = {}
                    supported_interpolations = coverage_description_element.find('.//supportedInterpolations', namespaces=coverage_namespaces)
                    interpolations['default'] = supported_interpolations.attrib.get('default', None)
                    interpolations['supported'] = [fmt.text for fmt in supported_interpolations.findall('interpolationMethod', namespaces=coverage_namespaces)]
            coverages[name] = Coverage(name, label,description, spatial_domain, range_sets, crs_info, formats, interpolations)
        return coverages
    
    def _get_coverages_v2(self):
        coverages = {}
        coverage_elements = self.root.findall('.//wcs:CoverageSummary', namespaces=self.namespaces)
        for coverage in coverage_elements:
            coverageID = coverage.find('wcs:CoverageId', namespaces=self.namespaces).text
            response = requests.get(self.url + f'?service=WCS&version={self.version}&request=DescribeCoverage&coverageID={coverageID}', timeout=30)
            if response.status_code == 200:
                coverage_description_xml = response.content
                coverage_description_root = ET.fromstring(coverage_description_xml)
                coverage_namespaces = self._extract_namespaces(io.BytesIO(response.content))
                coverage_description_elements = coverage_description_root.findall('.//wcs:CoverageDescription', namespaces=coverage_namespaces)
                for coverage_description_element in coverage_description_elements:
                    spatial_domain = {'Envelopes': [], 'RectifiedGrids': []}
                    envelopes = coverage_description_element.findall('.//gml:Envelope', namespaces=coverage_namespaces)
                    for envelope in envelopes:
                        bbox, srs_name, axis_envelope = self._read_envelope(envelope)
                        spatial_domain['Envelopes'].append({'bbox':bbox, 'srsName':srs_name, 'axisNames': axis_envelope})
                        
                    rectified_grids = coverage_description_element.findall('.//gml:RectifiedGrid', namespaces=coverage_namespaces)
                    for grid in rectified_grids:
                        grid_limits = grid.find('.//gml:GridEnvelope', namespaces=coverage_namespaces)
                        low = None
                        high = None
                        if grid_limits is not None:
                            low = [int(coord) for coord in grid_limits.findtext('.//gml:low', namespaces=coverage_namespaces).split()]
                            high = [int(coord) for coord in grid_limits.findtext('.//gml:high', namespaces=coverage_namespaces).split()]
                        axis_names = grid.findtext('gml:axisLabels', namespaces=coverage_namespaces)
                        if axis_names:
                            axis_names = axis_names.split()
                        origin = grid.findtext('.//gml:origin/gml:Point/gml:pos', namespaces=coverage_namespaces)
                        if origin is not None:
                            origin = [float(coord) for coord in origin.split()]
                        offset_vectors = []
                        for offset in grid.findall('gml:offsetVector', namespaces=coverage_namespaces):
                                offset_vectors.append([float(coord) for coord in offset.text.split()])
                        spatial_domain['RectifiedGrids'].append(
                            {
                                'limits': {'low': low, 'high': high},
                                'axisNames': axis_names,
                                'origin': origin,
                                'offsetVectors': offset_vectors
                            }
                        )
                        range_sets = []
                        rangesets = coverage_description_element.findall('.//gmlcov:rangeType/swe:DataRecord', namespaces=coverage_namespaces)
                        for rangeset in rangesets:
                            field = rangeset.find('swe:field', namespaces=coverage_namespaces)
                            if field:
                                field = field.attrib.get('name', None)
                                units = rangeset.find('.//swe:uom', namespaces=coverage_namespaces)
                                if units is not None:
                                    units = units.attrib.get('code', None)
                            range_sets.append({'name':field, 'uom':units})
                    coverages[coverageID] = Coverage(coverageID, None, None, spatial_domain, range_sets, self.get_supported_crs(), self.get_supported_formats(), None)

        return coverages
    
    def get_service_info(self) -> Optional[Dict[str, str]]:
        """
        Retrieves general information about the service.

        Returns:
            (Optional[Dict[str, str]]): A dictionary containing 'title', 'abstract', and 'version' of the service, or None if not found.
        """
        # version: 1.0.0
        service_identification = self.root.find('.//Service', namespaces=self.namespaces)
        if service_identification is not None:
            service_title = service_identification.find('name', namespaces=self.namespaces).text
            service_abstract = service_identification.find('label', namespaces=self.namespaces).text
            service_description = service_identification.find('description', namespaces=self.namespaces).text
            return {
                'name': service_title,
                'label': service_abstract,
                'description': service_description
            }
        # version:2.0.1
        service_identification = self.root.find('ows:ServiceIdentification', namespaces=self.namespaces)
        if service_identification is not None:
            service_title = service_identification.find('ows:Title', namespaces=self.namespaces).text
            service_abstract = service_identification.find('ows:Abstract', namespaces=self.namespaces).text
            service_version = service_identification.find('ows:ServiceTypeVersion', namespaces=self.namespaces).text
            return {
                'title': service_title,
                'abstract': service_abstract,
                'version': service_version
            }
        return None
        
    def get_operations(self) -> List[str]:
        """
        Retrieves available operations from the WCS capabilities document.

        Returns:
            List[str]: A list of operation names available in the service.
        """
        # version 1.0.0
        operations = self.root.find('.//Request', namespaces=self.namespaces)
        if operations:
            return [op.tag for op in operations]
        # version 2.0.1
        operations = self.root.findall('.//ows:OperationsMetadata/ows:Operation', namespaces=self.namespaces)
        if operations:
            return [op.get('name') for op in operations]
        
        return None
    
    def get_supported_formats(self):
        """
        Retrieves the list of supported formats for the WCS service.

        For WCS version 1.0.0, this method raises a ValueError as supported formats 
        are described in the DescribeCoverage request.

        For other versions, it returns a list of supported formats extracted from the WCS capabilities document.

        Returns:
            List[str]: A list of supported formats.

        Raises:
            ValueError: If the WCS version is '1.0.0', as supported formats are retrieved through DescribeCoverage.

        Example:
            >>> formats = wcs_service.get_supported_formats()
            >>> print(formats)  
            ['image/tiff', 'application/json']
        """
        if self.version == '1.0.0':
            return ValueError('For version 1.0.0 the supported formats are described in DescribeCoverage')
        
        formats = self.root.findall('.//wcs:ServiceMetadata/wcs:formatSupported', namespaces=self.namespaces)
        return [format.text for format in formats]
    
    def get_supported_crs(self) -> List[str]:
        """
        Retrieves the list of supported Coordinate Reference Systems (CRS) for the WCS service.

        For WCS version 1.0.0, this method raises a ValueError as supported CRS values 
        are described in the DescribeCoverage request.

        For other versions, it returns a list of supported CRS values extracted from the WCS capabilities document.

        Returns:
            List[str]: A list of supported CRS values.

        Raises:
            ValueError: If the WCS version is '1.0.0', as supported CRS values are retrieved through DescribeCoverage.

        Example:
            >>> crs_list = wcs_service.get_supported_crs()
            >>> print(crs_list)  
            ['EPSG:4326', 'EPSG:3857']
        """
        if self.version == '1.0.0':
            return ValueError('For version 1.0.0 the supported formats are described in DescribeCoverage')

        crs_elems = self.root.findall('.//wcs:ServiceMetadata/wcs:Extension/crs:CrsMetadata/crs:crsSupported', namespaces=self.namespaces)
        return [crs.text for crs in crs_elems]
    
    def list_coverages(self) -> Dict[str, Dict[str, Any]]:
        """
        Lists available coverages in the WCS service as defined in the capabilities document.

        This method supports both WCS version 1.0.0 and 2.0.1. For each version, it extracts coverage details
        and returns them in a dictionary format.

        For version 1.0.0, the coverages include attributes such as:
        - 'label': The human-readable label of the coverage.
        - 'description': A brief description of the coverage.
        - 'bbox': The bounding box (in lon-lat coordinates) for the coverage.
        - 'srsName': The spatial reference system used.

        For version 2.0.1, the coverages include:
        - 'subtype': The subtype of the coverage.

        Returns:
            (Dict[str, Dict[str, Any]]): A dictionary where each key is the coverage name or ID, and the value is another dictionary
            containing coverage attributes depending on the WCS version:
                - For version 1.0.0: {'label', 'description', 'bbox', 'srsName'}
                - For version 2.0.1: {'subtype'}
        
        Example:
            >>> coverages = wcs_service.list_coverages()
            >>> print(coverages)
            ... Output for version 1.0.0 might look like:
            ... {
            ...   'coverage1': {
            ...       'label': 'Coverage 1',
            ...       'description': 'Description of coverage 1',
            ...       'bbox': [-10.0, 40.0, 10.0, 50.0],
            ...       'srsName': 'EPSG:4326'
            ...   },
            ...   'coverage2': {
            ...       'label': 'Coverage 2',
            ...       'description': 'Description of coverage 2',
            ...       'bbox': [-20.0, 30.0, 20.0, 60.0],
            ...       'srsName': 'EPSG:4326'
            ...   }
            ... }
        """
        coverage_dict = {}
        # version 1.0.0
        coverage_elements = self.root.findall('.//CoverageOfferingBrief', namespaces=self.namespaces)
        for coverage in coverage_elements:
            name = coverage.find('name', namespaces=self.namespaces).text
            label = coverage.find('label', namespaces=self.namespaces).text
            description = coverage.find('description', namespaces=self.namespaces).text
            # Find the lonLatEnvelope element
            lon_lat_envelope = coverage.find('lonLatEnvelope', namespaces=self.namespaces)
            bbox, srs_name = self._read_envelope(lon_lat_envelope)
            coverage_dict[name] = {
                    'label': label,
                    'description': description,
                    'bbox': bbox,
                    'srsName': srs_name
                }
        if coverage_dict:
            return coverage_dict
        
        # version 2.0.1
        coverage_elements = self.root.findall('.//wcs:Contents/wcs:CoverageSummary', namespaces=self.namespaces)
        for coverage in coverage_elements:
            name = coverage.find('wcs:CoverageId', namespaces=self.namespaces).text
            subtype = coverage.find('wcs:CoverageSubtype', namespaces=self.namespaces).text
            coverage_dict[name] = {
                    'subtype': subtype,
                }
        if coverage_dict:
            return coverage_dict
        
        return None
    
    def describe_coverage(self, coverageID: str) -> Optional[Coverage]:
        """
        Retrieves detailed information about a specific coverage.

        Parameters:
            coverageID (str): The name of the coverage to query.

        Returns:
            Optional[Coverage]: An object with details about the coverage, or None if not found.
        """
        return self.coverages.get(coverageID)


class OpenAPIDoc:
    """
    A class to interact with an OpenAPI document and extract useful information, such as collections, paths, parameters, and queryables, 
    for different types of OGC APIs: coverages, features, or maps.

    Attributes:
        url (str): The URL of the OpenAPI specification or OGC collection endpoint. Examples include:
            - Coverages API: 'https://api-coverages.idee.es/collections'
            - Features API: 'https://api-features.idee.es/collections'
            - Maps API: 'https://api-maps.idee.es/collections'
        
        spec (Dict): The OpenAPI specification fetched from the provided URL.

    Methods:
        _detect_api_type() -> Optional[str]:
            Detect whether the API is a Features, Coverages, or Maps API based on paths.
        fetch_openapi_spec() -> Optional[Dict]:
            Fetch the OpenAPI document from the specified URL.
        validate_spec() -> None:
            Validate the OpenAPI specification using openapi-spec-validator.
        get_info() -> Dict:
            Retrieve general information about the API from the OpenAPI document.
        get_paths() -> Dict[str, Dict[str, Any]]:
            Retrieve all available paths from the OpenAPI document.
        get_collections() -> List[str]:
            Extract available collections from the API paths.
        get_operations() -> List[str]:
            Get a list of available operations (paths) from the OpenAPI document.
        get_queryables() -> Dict[str, Dict[str, Dict]]:
            Retrieve all queryable parameters for each operation from the OpenAPI document.
        get_operation_queryables(operation: str) -> Optional[Dict[str, Dict]]:
            Get queryable parameters specific to a given operation.
        get_parameters() -> Dict[str, Dict[str, Dict]]:
            Retrieve all parameters, including resolved references, from the OpenAPI document.
        resolve_parameter(param: Dict) -> Tuple[Optional[str], Dict]:
            Resolve parameter references (if applicable) and return the actual parameter definition.
        get_operation_parameters(operation: str) -> Optional[Dict[str, Dict]]:
            Get parameters specific to a given operation.
        describe_collection(collectionId: str) -> Dict:
            Retrieve detailed information about a specific collection.
        is_output_crs_supported(collectionId: str, crs: str) -> bool:
            Checks if a specified Coordinate Reference System (CRS) is supported by a collection.
    """
    logger:logging.Logger = logging.getLogger(__name__)
    
    def __init__(self, url:str) -> None:
        """
        Initialize the OpenAPIDoc object by fetching the OpenAPI specification.

        Parameters:
            url (str): The URL of the OpenAPI specification. Examples:
                - 'https://api-coverages.idee.es/collections'
                - 'https://api-features.idee.es/collections'
                - 'https://api-maps.idee.es/collections'
        """
        self.url = url
        self.spec = self.fetch_openapi_spec()
        
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
        
    def _detect_api_type(self) -> Optional[str]:
        """
        Detect if the API is a Features API, a Coverages API, or a Maps API based on the available paths.

        The detection is based on patterns in the paths:
        - '/items' indicates a Features API.
        - '/coverage' indicates a Coverages API.
        - '/map' indicates a Maps API.

        Returns:
            Optional[str]: Returns 'items' for Features API, 'coverage' for Coverages API, 'map' for Maps API, or None if the type cannot be detected.
        """
        paths = self.get_paths()
        
        if any(path.endswith('/items') for path in paths):
            return 'items'
        if any(path.endswith('/coverage') for path in paths):
            return 'coverage'
        if any(path.endswith('/map') for path in paths):
            return 'map'
        
        return None

    def fetch_openapi_spec(self) -> Union[Dict, None]:
        """
        Fetch the OpenAPI specification from the provided URL.

        Returns:
            (Union[Dict, None]): The OpenAPI document as a dictionary, or None if the request fails.
        """
        openapi_url = self.url + '/openapi?f=json'
        self.openapi = openapi_url
        response = requests.get(openapi_url)
        if response.status_code == 200:
            return response.json()

        openapi_url = self.url + '/api?f=json'
        self.openapi = openapi_url
        response = requests.get(openapi_url)
        if response.status_code == 200:
            return response.json()
        
        
        return None

    def validate_spec(self) -> None:
        """
        Validate the OpenAPI specification using openapi-spec-validator.
        
        Raises:
            Exception: If the OpenAPI specification is invalid.
        """
        try:
            validate_spec(self.spec)
            print("OpenAPI specification is valid.")
        except Exception as e:
            print("OpenAPI specification is invalid:", e)

    def get_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve general information about the API.

        Returns:
            (Dict[str, Dict[str, Any]]): The 'info' section from the OpenAPI document.
        """
        return self.spec.get('info', {})

    def get_paths(self) -> Dict:
        """
        Retrieve all available paths from the OpenAPI document.

        Returns:
            Dict: A dictionary of available paths.
        """
        return self.spec.get('paths', {})
    
    def get_collections(self) -> List[str]:
        """
        Extract the list of available collections from the OpenAPI paths.

        Returns:
            List[str]: A list of collection IDs extracted from the paths.
        """
        # Extract collections from paths in the OpenAPI spec
        collections = []
        response = requests.get(f'{self.url}/collections?f=json')
        if response.status_code == 200:
            # Loop through paths and identify those containing 'collections'
            for collection in response.json().get('collections'):
                collections.append(collection.get('id'))
            
            return collections
    
    def get_operations(self) -> List[str]:
        """
        Get a list of available operations (paths) from the OpenAPI document.

        Returns:
            List[str]: A list of operation paths.
        """
        return list(self.get_paths().keys())

    def get_queryables(self) -> Dict[str, Dict[str, Dict]]:
        """
        Retrieve queryable parameters for each operation from the OpenAPI document.

        Returns:
            (Dict[str, Dict[str, Dict]]): A dictionary where each key is a path, and the value is another dictionary of queryable parameters for that path.
        """
        queryables = {}
        paths = self.get_paths()

        for path, methods in paths.items():
            for method, details in methods.items():
                parameters = details.get('parameters', [])
                for param in parameters:
                    name, resolved_param = self.resolve_parameter(param)
                    if resolved_param.get('in') == 'query':
                        queryables.setdefault(path, {})[resolved_param.get('name')] = resolved_param

        return queryables
    
    def get_operation_queryables(self, operation:str) -> Optional[Dict[str, Dict]]:
        """
        Get queryable parameters for a specific operation.

        Parameters:
            operation (str): The operation path for which to retrieve queryable parameters.

        Returns:
            (Optional[Dict[str, Dict]]): A dictionary of queryable parameters for the specified operation, or None if no queryables exist for that operation.
        """
        return self.get_queryables().get(operation)

    def get_parameters(self) -> Dict[str, Dict[str, Dict]]:
        """
        Retrieve all parameters from the OpenAPI document, including those referenced in the 'components' section.

        Returns:
            (Dict[str, Dict[str, Dict]]): A dictionary where each key is a path, and the value is another dictionary of parameters for that path.
        """
        parameters = {}
        paths = self.get_paths()

        for path, methods in paths.items():
            for method, details in methods.items():
                parameters_list = details.get('parameters', [])
                for param in parameters_list:
                    name, resolved_param = self.resolve_parameter(param)
                    if resolved_param.get('in') != 'query':
                        parameters.setdefault(path, {})[name] = resolved_param

        return parameters

    def resolve_parameter(self, param: Dict) -> Tuple[Optional[str], Dict]:
        """
        Resolve a parameter reference from the 'components' section and return the actual parameter definition.

        Parameters:
            param (Dict): The parameter object, which may contain a reference ('$ref') to a component.

        Returns:
            (Tuple[Optional[str], Dict]): A tuple containing the parameter name and its definition, or (None, param) if the parameter is not a reference.
        """
        
        if '$ref' in param:
            ref = param['$ref']
            # Extract the parameter definition from the components
            ref_key = ref.split('/')[-1]  # Get the last part of the reference
            return (ref_key.replace('-', '_'), self.spec['components']['parameters'].get(ref_key, {}))
        return None, param
    
    def get_operation_parameters(self, operation:str) -> Optional[Dict[str, Dict]]:
        """
        Get parameters for a specific operation path.

        Parameters:
            operation (str): The operation path for which to retrieve parameters.

        Returns:
            Optional[Dict[str, Dict]]: A dictionary of parameters for the specified operation, or None if no parameters exist for that operation.
        """
        return self.get_parameters().get(operation)
    
    def describe_collection(self, collectionId:str) -> Dict:
        """
        Retrieve detailed information about a specific collection.

        Parameters:
            collectionId (str): The identifier of the collection to describe.

        Returns:
            Dict: A dictionary containing details about the specified collection, or an empty dictionary if the request fails.
        """
        response = requests.get(f'{self.url}/collections/{collectionId}?f=json', timeout=30)
        if response.status_code == 200:
            return response.json()
        
        return {}
    
    def is_output_crs_supported(self, collectionId: str, crs: str) -> bool:
        """
        Checks if a specified Coordinate Reference System (CRS) is supported by a collection.

        Parameters:
            collectionId (str): The identifier of the collection to check.
            crs (str): The CRS URI to check for support.

        Returns:
            bool: True if the CRS is supported by the collection, False otherwise.

        Raises:
            ValueError: If the CRS is not provided in URI notation.
        """
        if crs.startswith('http://www.opengis.net/def/crs/'):
            supported = self.describe_collection(collectionId=collectionId).get('crs', [])
            return crs in supported
        else:
            self.log('The crs must be a uri notation.', logging.CRITICAL)
            raise ValueError('The crs must be a uri notation.')
