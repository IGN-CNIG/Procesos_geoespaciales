# Capabilities Module Documentation

## Overview
The `capabilities.py` module defines classes that represent the capabilities of various INSPIRE services. These classes provide functionality for accessing and parsing service capabilities, allowing users to understand the features and operations supported by each service.

## Classes

### 1. InspireDownloadService
Base class for INSPIRE Capabilities Documents.

#### Attributes
  - `logger` (logging.Logger): A logger instance for logging messages.
  - `url` (str): The base URL of the geospatial service.
  - `service_type` (str): The type of service (WFS, WCS, etc.).
  - `version` (str): The version of the service capabilities document.
  - `tree` (Optional[ElementTree]): The parsed XML tree of the capabilities document.
  - `root` (Optional[Element]): The root element of the XML tree.
  - `namespaces` (Dict[str, str]): A dictionary of XML namespaces extracted from the capabilities document.

#### Methods
  - **`log(message: str, level: Optional[str] = logging.INFO) -> None`**: Logs a message with the specified logging   level (INFO by default). If no logger is available, it prints the message to the console.
  - **`_fetch_capabilities() -> None`**: Fetches the capabilities document from the specified service URL and parses   it into an XML tree. Raises an exception if fetching fails.
  - **`_extract_namespaces(xml_content: io.BytesIO) -> Dict[str, str]`**: Extracts and returns namespaces from the   given XML content. This method is a static method.
  - **`get_service_type() -> Optional[str]`**: Returns the type of the service (e.g., WFS or WCS). This method is   tied to the instance as it relies on instance attributes.
  - **`get_crs_identifier(crs_uri: str) -> Optional[str]`**: Class method to fetch and parse a CRS document from the   given URI, returning the CRS identifier in 'codeSpace:identifier' format if found.
  - **`_read_envelope(envelope: ET.Element) -> Optional[Tuple[List[float], Optional[str]]]`**: Reads an envelope (bounding box) element from the capabilities document to extract its bounding coordinates and spatial reference system (SRS).

---

### 2. WFSCapabilities
A class to represent and interact with a Web Feature Service (WFS) capabilities document.

This class extends the `Capabilities` base class to provide specific functionalities for handling
WFS capabilities, including querying stored queries, feature types, and service constraints. 

#### Attributes
  - `service` (str): The type of service (e.g., 'WFS').
  - `version` (str): The WFS protocol version.
  - `url` (str): The URL of the WFS service endpoint.
  - `stored_queries` (dict): A dictionary of stored queries available in the WFS service.

#### Methods
  - **`_get_stored_queries() -> Optional[Dict[str, StoredQuery]]`**: Retrieves and parses stored queries available in the WFS service.
  - **`get_service_info() -> Optional[Dict[str, str]]`**: Retrieves general information about the WFS service, including title, abstract, and version.
  - **`get_operations() -> List[str]`**: Retrieves the available operations from the capabilities document.
  - **`get_parameters() -> Dict[str, Dict[str, Union[str, List[str]]]]`**: Queries and extracts parameters defined in the capabilities document, including allowed values and default values.
  - **`get_constraints() -> Dict[str, Dict[str, Union[str, List[str]]]]`**:  Retrieves service constraints from the capabilities document, including allowed values and default values.
  - **`query_constraint(constraint_name: str) -> Optional[Dict[str, Union[str, List[str]]]]`**: Queries details of a specific constraint by name, including allowed values and default value if available.
  - **`get_feature_types() -> List[Dict[str, str]]`**: Retrieves all available feature types in the WFS service, including their names and titles.
  - **`query_feature_type(feature_name: str) -> Optional[Dict[str, Union[str, List[str]]]]`**: Queries details for a specific feature type, including CRS information and output formats.
  - **`list_stored_queries() -> List[Dict[str, str]]`**: Lists stored queries available in the WFS capabilities document with their IDs and titles.

#### Example
```python
wfs_capabilities_ = WCSCapabilities(service='WFS', version='2.0.0', url='https://www.ideandalucia.es/wfs-nga-inspire/services')
info = wfs_capabilities_.get_service_info()
operations = wfs_capabilities_.get_operations()
stored_queries = wfs_capabilities.list_stored_queries()
```

---

### 3. WCSCapabilities
Represents the capabilities of a Web Coverage Service (WCS).

#### Attributes
  - `service` (str): The type of service (e.g., 'WCS').
  - `version` (str): The WCS protocol version.
  - `url` (str): The URL of the WCS service endpoint.
  - `coverages` (list): A list of coverages supported by the service.

#### Methods
  - **`_get_coverages() -> List[Dict[str, Coverage]]`**: Internal method to parse and retrieve all coverages from the WCS capabilities document and create `Coverage` objects.
  - **`get_service_info() -> Optional[Dict[str, str]]`**: Retrieves general information about the WCS service, including title, label, and description.
  - **`get_operations() -> List[str]`**: Retrieves a list of operations that the WCS service supports.
  - **`get_supported_formats() -> List[str]`**: Retrieves the list of supported formats for the WCS service.
  - **`get_supported_crs(self) -> List[str]`**: Retrieves the list of supported Coordinate Reference Systems (CRS) for the WCS service.
  - **`list_coverages() -> Dict[str, Dict[str, Any]]`**: Lists coverages available in the WCS capabilities document, returning a dictionary with coverage
        names as keys and coverage metadata (label, description, bounding box, and SRS) as values.
  - **`describe_coverage(self, coverageID: str) -> Optional[Coverage]`**: Retrieves detailed information about a specific coverage.

#### Example
```python
wcs_capabilities_ = WCSCapabilities(service='WCS', version='2.0.1', url='https://servicios.idee.es/wcs-inspire/mdt')
info = wcs_capabilities_.get_service_info()
operations = wcs_capabilities_.get_operations()
formats = wcs_capabilities_.get_supported_formats()
coverages = wcs_capabilities_.list_coverages()
```

---

### 4. OpenAPIDoc
A class to interact with an OpenAPI document and extract useful information, such as collections, paths, parameters, and queryables, for different types of OGC APIs: coverages, features, or maps.

#### Attributes
- `logger (logging.Logger)`: A logger instance for logging messages.
- `url (str)`: The URL of the OpenAPI specification or OGC collection endpoint.
- `spec (Dict)`: The OpenAPI specification fetched from the provided URL.

#### Methods
  - log(message: str, level: Optional[int] = logging.INFO) -> None: Logs a message at the specified logging level if the logger is active, otherwise prints it to the console.
  - **`_detect_api_type() -> Optional[str]`**: Detect whether the API is a Features, Coverages, or Maps API based on paths.
  - **`fetch_openapi_spec() -> Optional[Dict]`**: Fetch the OpenAPI document from the specified URL.
  - **`validate_spec() -> None`**: Validate the OpenAPI specification using openapi-spec-validator.
  - **`get_info() -> Dict`**: Retrieve general information about the API from the OpenAPI document.
  - **`get_paths() -> Dict[str, Dict[str, Any]]`**: Retrieve all available paths from the OpenAPI document.
  - **`get_collections() -> List[str]`**: Extract available collections from the API paths.
  - **`get_operations() -> List[str]`**: Get a list of available operations (paths) from the OpenAPI document.
  - **`get_queryables() -> Dict[str, Dict[str, Dict]]`**: Retrieve all queryable parameters for each operation from the OpenAPI document.
  - **`get_operation_queryables(operation: str) -> Optional[Dict[str, Dict]]`**: Get queryable parameters specific to a given operation.
  - **`get_parameters() -> Dict[str, Dict[str, Dict]]`**: Retrieve all parameters, including resolved references, from the OpenAPI document.
  - **`resolve_parameter(param: Dict) -> Dict`**: Resolve a parameter definition that may include references.

#### Example
```python
openapi_doc = OpenAPIDoc(url='https://api-features.ign.es', name='IGN')
info = openapi_doc.get_info()
paths = openapi_doc.get_paths()
collections = openapi_doc.get_collections()
```