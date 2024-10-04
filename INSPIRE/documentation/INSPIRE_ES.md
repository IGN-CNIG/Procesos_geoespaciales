# Documentación del Módulo Inspire

## Descripción general
Este módulo proporciona funcionalidad para interactuar con varios servicios de descarga INSPIRE, incluidos los servicios WCS, Atom y OGC API. Cada clase ofrece métodos para recuperar datos geoespaciales y gestionar conexiones a estos servicios.

## Clases

### 1. InspireDownloadService
Clase base para los Servicios de Descarga INSPIRE.

#### Atributos
  - `service` (str): El tipo de servicio (p. ej., 'WCS', 'ATOM', 'OGCAPI').
  - `ds` (ogr.DataSource): La fuente de datos OGR para acceder a las capas del servicio.

#### Métodos
  - `log(message: str, level: int = logging.INFO)`: Registra un mensaje en un nivel de registro específico.
  - `_set_ds(ds)`: Establece la fuente de datos para OGR.
  - `add_errors_to_feature(feature)`: Agrega manejo de errores a las características.

---

### 2. WFSService
Representa un Servicio de Descarga Inspire WFS (Servicio de Características Web) para obtener características geográficas.

#### Atributos
  - `source` (str): La URL del punto final del servicio WFS.
  - `name` (str): Un nombre para identificar la instancia del servicio WFS.
  - `version` (Opcional[str]): La versión del protocolo WFS a utilizar (por defecto es '2.0.0').
  - `max_features` (Opcional[int]): Número máximo de características a recuperar en una sola solicitud (por defecto es 5000).
  - `timeout` (Opcional[int]): Duración del tiempo de espera en segundos para las solicitudes al servicio WFS (por defecto es 90).
  - `capabilities`: Una instancia que representa las capacidades del servicio WFS.
  - `stored_queries` (dict): Un diccionario que contiene las consultas almacenadas disponibles en el servicio WFS.

#### Métodos
  - `get_feature_from_stored_query(STORED_QUERY: str, **args) -> Generator[ogr.Feature, None, None]`: Recupera características del servicio WFS utilizando una consulta almacenada.
  - `get_feature_parameters() -> Dict[str, bool]`: Recupera los parámetros de características compatibles con el servicio WFS para la versión dada.
  - `get_feature(SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]`: Recupera características del servicio WFS basadas en parámetros especificados.

#### Ejemplo
```python
wfs = WFSService(source='https://www.ideandalucia.es/wfs-nga-inspire/services', name=name, version='2.0.0', max_features=5000, timeout=90)
wfs.get_feature(typeNames='gn:NamedPlace', srsName='EPSG:25830', SQL_PREDICATE=f"beginLifespanVersion >= '2024-01-01' and beginLifespanVersion < '2024-03-01'")
for feature in features:
    print(feature)
```

---

### 3. WCSService
Representa un Servicio de Descarga WCS INSPIRE.

#### Atributos
  - `source` (str): La URL del servicio WCS.
  - `name` (str): El nombre del servicio WCS.
  - `version` (str): La versión del WCS (por defecto: '2.0.1').
  - `max_coverages` (int): Número máximo de coberturas a recuperar (por defecto: 100).
  - `timeout` (int): Tiempo de espera para las solicitudes (por defecto: 90 segundos).
  - `capabilities`: Una instancia de `WCSCapabilities`.

#### Métodos
  - `get_coverage_parameters() -> Dict[str, bool]`: Recupera los parámetros de cobertura compatibles con el servicio.
  - `get_coverage(filename: Optional[str] = None, **args) -> None`: Recupera coberturas del servicio WCS.

#### Ejemplo
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
Representa un Servicio de Descarga Atom INSPIRE.

#### Atributos
  - `source` (str): La URL del feed Atom.
  - `name` (str): Un nombre para identificar la instancia del servicio Atom.

#### Métodos
  - `is_atom() -> bool`: Verifica si la fuente de datos es un servicio Atom.
  - `recurse_links(parent_link: Optional[str] = None, xml: Optional[str] = None) -> Generator[str, None, None]`: Extrae recursivamente enlaces de conjuntos de datos de un feed Atom.
  - `_get_ogr_feature(gml: str, typeNames: str) -> Generator[ogr.Feature, None, None]`: Analiza datos GML y extrae características como objetos OGR Feature.
  - `get_feature(typeNames: str, FILES: Optional[str] = None) -> Generator[ogr.Feature, None, None]`: Recupera características geoespaciales del servicio Atom.

#### Ejemplo
```python
atom = AtomService(source='https://geoserveis.ide.cat/servei/catalunya/inspire-noms-geografics/atom/inspire-noms-geografics.atom.xml', name='Cataluña')
features = atom.get_feature(typeNames='NamedPlace')
for feature in features:
    print(feature)
```

---

### 5. OGCAPIService
Obtiene características de un Servicio de Descarga API OGC.

#### Atributos
  - `source` (str): La URL base del servicio OGC API.
  - `name` (str): El nombre del servicio OGC API.
  - `ds` (ogr.DataSource): La fuente de datos OGR para acceder a capas desde la API OGC.

#### Métodos
  - **`get_collections() -> List[str]`**:
      Recupera una lista de todos los nombres de colecciones (capas) disponibles en el servicio OGC API.
  - **`get_layer(collectionId: str) -> ogr.Layer`**:
      Obtiene una capa específica (colección) por su identificador desde el servicio OGC API.
  - **`get_available_parameters() -> Dict[str, str]`**:
      Recupera los parámetros de consulta disponibles de la documentación OpenAPI del servicio OGC API.
  - **`get_queryable_properties(collectionId: str) -> Dict[str, str]`**:
      Recupera las propiedades consultables para una colección dada.
  - **`is_crs_supported(collectionId: str, crs: str) -> bool`**:
      Verifica si un Sistema de Referencia de Coordenadas (CRS) especificado es compatible con una colección.
  - **`set_layer_crs(layer: ogr.Layer, crs: str) -> None`**:
      Establece el CRS para una capa dada.
  - **`build_filter(collectionId: str, **args) -> str`**:
      Construye una cadena de filtro SQL basada en los argumentos proporcionados.
  - **`get_feature(collectionId: str, SQL_PREDICATE: Optional[str] = None, **args) -> Generator[ogr.Feature, None, None]`**:
      Recupera características de una colección especificada, aplicando filtros opcionales.
  - **`get_coverage(collectionId: str, filename: Optional[str] = None, **args) -> Optional[Dict]`**:
      Obtiene datos de cobertura del servicio OGC API, guardándolos opcionalmente en un archivo.

#### Ejemplo
```python
API = OGCAPIService(source='https://api-features.idee.es/', name='Address')
features = API.get_feature(collectionId='address', crs='http://www.opengis.net/def/crs/EPSG/0/25830', inspireId_localId='AD_ADDRESS_PPK_010010016525')
for feature in features:
    print(feature)
```
