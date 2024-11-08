# Inspire Module Documentation

## Overview
This module provides functionality for interacting with various INSPIRE download services, including WCS, Atom, and OGC API services. Each class offers methods for retrieving geospatial data and managing connections to these services.

## Classes

### 1. InspireDownloadService
Base class for INSPIRE Download Services.

#### Attributes
  - `service` (str): The type of the service (e.g., 'WCS', 'ATOM', 'OGCAPI').
  - `ds` (ogr.DataSource): The OGR data source for accessing layers from the service.

#### Methods
  - `log(message: str, level: int = logging.INFO)`: Log a message at a specific logging level.
  - `_set_ds(ds)`: Set the data source for OGR.
  - `add_errors_to_feature(feature)`: Add error handling to features.

---

### 2. WFSService
Represents an Inspire WFS (Web Feature Service) Download Service for fetching geographical features.

#### Attributes
  - `source` (str): The URL of the WFS service endpoint.
  - `name` (str): A name for identifying the WFS service instance.
  - `version` (Optional[str]): The WFS protocol version to use (default is '2.0.0').
  - `max_features` (Optional[int]): Maximum number of features to retrieve in a single request (default is 5000).
  - `timeout` (Optional[int]): Timeout duration in seconds for requests to the WFS service (default is 90).
  - `capabilities`: An instance representing the capabilities of the WFS service.
  - `stored_queries` (dict): A dictionary holding stored queries available in the WFS service.

#### Methods
  - `get_feature_from_stored_query(STORED_QUERY: str, **args) -> Generator[ogr.Feature, None, None]`: Fetches   features from the WFS service using a stored query.
  - `get_feature_parameters() -> Dict[str, bool]`: Retrieves the feature parameters supported by the WFS service for   the given version.
  - `get_feature(SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]`: Fetches features from the WFS service based on specified parameters.

#### Example
```python
wfs = WFSService(source='https://www.ideandalucia.es/wfs-nga-inspire/services', name=name, version='2.0.0', max_features=5000, timeout=90)
wfs.get_feature(typeNames='gn:NamedPlace', srsName='EPSG:25830', SQL_PREDICATE=f"beginLifespanVersion >= '2024-01-01' and beginLifespanVersion < '2024-03-01'")
for feature in features:
    print(feature)
```

---

### 3. WCSService
Represents an INSPIRE WCS Download Service.

#### Attributes
  - `source` (str): The URL of the WCS service.
  - `name` (str): The name of the WCS service.
  - `version` (str): The WCS version (default: '2.0.1').
  - `max_coverages` (int): Maximum number of coverages to retrieve (default: 100).
  - `timeout` (int): Timeout for requests (default: 90 seconds).
  - `capabilities`: An instance of `WCSCapabilities`.

#### Methods
 - `get_coverage_parameters() -> Dict[str, bool]`: Retrieves coverage parameters supported by the service.
  - `get_coverage(filename: Optional[str] = None, **args) -> None`: Fetches coverages from the WCS service.

#### Example
```python
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
```

---

### 4. AtomService
Represents an INSPIRE Atom Download Service.

#### Attributes
  - `source` (str): The URL of the Atom feed.
  - `name` (str): A name for identifying the Atom service instance.

#### Methods
  - `is_atom() -> bool`: Checks if the data source is an Atom service.
  - `recurse_links(parent_link: Optional[str] = None, xml: Optional[str] = None) -> Generator[str, None, None]`:   Recursively extracts dataset links from an Atom feed.
  - `_get_ogr_feature(gml: str, typeNames: str) -> Generator[ogr.Feature, None, None]`: Parses GML data and extracts   features as OGR Feature objects.
  - `get_feature(typeNames: str, FILES: Optional[str] = None) -> Generator[ogr.Feature, None, None]`: Retrieves geospatial features from the Atom service.

#### Example
```python
atom = AtomService(source='https://geoserveis.ide.cat/servei/catalunya/inspire-noms-geografics/atom/inspire-noms-geografics.atom.xml', name='Cataluña')
features = atom.get_feature(typeNames='NamedPlace')
for feature in features:
    print(feature)
```

---

### 5. OGCAPIService
Fetches features from an OGC API Download Service.

#### Attributes
  - `source` (str): The base URL of the OGC API service.
  - `name` (str): The name of the OGC API service.
  - `ds` (ogr.DataSource): The OGR data source for accessing layers from the OGC API.

#### Methods
  - **`get_collections() -> List[str]`**:
      Retrieves a list of all collection names (layers) available in the OGC API service.
  - **`get_layer(collectionId: str) -> ogr.Layer`**:
      Fetches a specific layer (collection) by its identifier from the OGC API service.
  - **`get_available_parameters() -> Dict[str, str]`**:
      Retrieves available query parameters from the OGC API service's OpenAPI documentation.
  - **`get_queryable_properties(collectionId: str) -> Dict[str, str]`**:
      Retrieves the queryable properties for a given collection.
  - **`is_crs_supported(collectionId: str, crs: str) -> bool`**:
      Checks if a specified Coordinate Reference System (CRS) is supported by a collection.
  - **`set_layer_crs(layer: ogr.Layer, crs: str) -> None`**:
      Sets the CRS for a given layer.
  - **`build_filter(collectionId: str, **args) -> str`**:
      Constructs a SQL filter string based on the provided arguments.
  - **`get_feature(collectionId: str, SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]`**:
      Retrieves features from a specified collection, applying optional filters.
  - **`get_coverage(collectionId: str, filename: Optional[str] = None, **args) -> Optional[Dict]`**:
      Fetches coverage data from the OGC API service, optionally saving it to a file.

#### Example
```python
API = OGCAPIService(source='https://api-features.idee.es/', name='Address')
features = API.get_feature(collectionId='address', crs='http://www.opengis.net/def/crs/EPSG/0/25830', inspireId_localId='AD_ADDRESS_PPK_010010016525')
for feature in features:
    print(feature)
```
