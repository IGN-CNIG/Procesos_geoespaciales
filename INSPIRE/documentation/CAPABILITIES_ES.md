# Documentación del Módulo de Capacidades

## Descripción general
El módulo `capabilities.py` define clases que representan las capacidades de varios servicios INSPIRE. Estas clases proporcionan funcionalidad para acceder y analizar los documentos de capacidades de los servicios, permitiendo a los usuarios comprender las características y operaciones que soporta cada servicio.

## Clases

### 1. InspireDownloadService
Clase base para los documentos de capacidades INSPIRE.

#### Atributos
  - `logger` (logging.Logger): Una instancia de logger para registrar mensajes.
  - `url` (str): La URL base del servicio geoespacial.
  - `service_type` (str): El tipo de servicio (WFS, WCS, etc.).
  - `version` (str): La versión del documento de capacidades del servicio.
  - `tree` (Optional[ElementTree]): El árbol XML parseado del documento de capacidades.
  - `root` (Optional[Element]): El elemento raíz del árbol XML.
  - `namespaces` (Dict[str, str]): Un diccionario de espacios de nombres XML extraídos del documento de capacidades.

#### Métodos
  - `log(message: str, level: Optional[str] = logging.INFO) -> None`: Registra un mensaje con el nivel de registro especificado (INFO por defecto). Si no hay un logger disponible, imprime el mensaje en la consola.
  - `_fetch_capabilities() -> None`: Obtiene el documento de capacidades desde la URL del servicio especificada y lo analiza en un árbol XML. Lanza una excepción si la obtención falla.
  - `_extract_namespaces(xml_content: io.BytesIO) -> Dict[str, str]`: Extrae y devuelve los espacios de nombres del contenido XML dado. Este método es estático.
  - `get_service_type() -> Optional[str]`: Devuelve el tipo de servicio (por ejemplo, WFS o WCS). Este método está vinculado a la instancia, ya que depende de los atributos de la instancia.
  - `get_crs_identifier(crs_uri: str) -> Optional[str]`: Método de clase para obtener y analizar un documento CRS desde la URI dada, devolviendo el identificador CRS en el formato 'codeSpace:identifier' si se encuentra.
  - `_read_envelope(envelope: ET.Element) -> Optional[Tuple[List[float], Optional[str]]]`: Lee un elemento envelope (caja delimitadora) del documento de capacidades para extraer sus coordenadas y el sistema de referencia espacial (SRS).

---

### 2. WFSCapabilities
Clase para representar e interactuar con un documento de capacidades del Servicio de Características Web (WFS).

Esta clase extiende la clase base `Capabilities` para proporcionar funcionalidades específicas para manejar capacidades de WFS, incluyendo consultas almacenadas, tipos de características y restricciones del servicio.

#### Atributos
  - `service` (str): El tipo de servicio (por ejemplo, 'WFS').
  - `version` (str): La versión del protocolo WFS.
  - `url` (str): La URL del punto final del servicio WFS.
  - `stored_queries` (dict): Un diccionario de consultas almacenadas disponibles en el servicio WFS.

#### Métodos
  - `_get_stored_queries() -> Optional[Dict[str, StoredQuery]]`: Recupera y analiza las consultas almacenadas disponibles en el servicio WFS.
  - `get_service_info() -> Optional[Dict[str, str]]`: Recupera información general sobre el servicio WFS, incluyendo título, resumen y versión.
  - `get_operations() -> List[str]`: Recupera las operaciones disponibles desde el documento de capacidades.
  - `get_parameters() -> Dict[str, Dict[str, Union[str, List[str]]]]`: Consulta y extrae los parámetros definidos en el documento de capacidades, incluyendo los valores permitidos y valores predeterminados.
  - `get_constraints() -> Dict[str, Dict[str, Union[str, List[str]]]]`: Recupera las restricciones del servicio desde el documento de capacidades, incluyendo valores permitidos y valores predeterminados.
  - `query_constraint(constraint_name: str) -> Optional[Dict[str, Union[str, List[str]]]]`: Consulta los detalles de una restricción específica por su nombre, incluyendo los valores permitidos y el valor predeterminado si está disponible.
  - `get_feature_types() -> List[Dict[str, str]]`: Recupera todos los tipos de características disponibles en el servicio WFS, incluyendo sus nombres y títulos.
  - `query_feature_type(feature_name: str) -> Optional[Dict[str, Union[str, List[str]]]]`: Consulta los detalles de un tipo de característica específico, incluyendo información de CRS y formatos de salida.
  - `list_stored_queries() -> List[Dict[str, str]]`: Lista las consultas almacenadas disponibles en el documento de capacidades WFS con sus identificadores y títulos.

#### Ejemplo
```python
wfs_capabilities_ = WCSCapabilities(service='WFS', version='2.0.0', url='https://www.ideandalucia.es/wfs-nga-inspire/services')
info = wfs_capabilities_.get_service_info()
operations = wfs_capabilities_.get_operations()
stored_queries = wfs_capabilities.list_stored_queries()
```

---

### 3. WCSCapabilities
Representa las capacidades de un Servicio de Coberturas Web (WCS).

#### Atributos
  - `service` (str): El tipo de servicio (por ejemplo, 'WCS').
  - `version` (str): La versión del protocolo WCS.
  - `url` (str): La URL del punto final del servicio WCS.
  - `coverages` (list): Una lista de coberturas soportadas por el servicio.

#### Métodos
  - `_get_coverages() -> List[Dict[str, Coverage]]`: Método interno para analizar y recuperar todas las coberturas del documento de capacidades WCS y crear objetos `Coverage`.
  - `get_service_info() -> Optional[Dict[str, str]]`: Recupera información general sobre el servicio WCS, incluyendo título, etiqueta y descripción.
  - `get_operations() -> List[str]`: Recupera una lista de operaciones que soporta el servicio WCS.
  - `get_supported_formats() -> List[str]`: Recupera la lista de formatos soportados por el servicio WCS.
  - `get_supported_crs() -> List[str]`: Recupera la lista de Sistemas de Referencia de Coordenadas (CRS) soportados por el servicio WCS.
  - `list_coverages() -> Dict[str, Dict[str, Any]]`: Lista las coberturas disponibles en el documento de capacidades WCS, devolviendo un diccionario con los nombres de las coberturas como claves y metadatos de coberturas (etiqueta, descripción, caja delimitadora y SRS) como valores.

#### Ejemplo
```python
wcs_capabilities_ = WCSCapabilities(service='WCS', version='2.0.1', url='https://servicios.idee.es/wcs-inspire/mdt')
info = wcs_capabilities_.get_service_info()
operations = wcs_capabilities_.get_operations()
formats = wcs_capabilities_.get_supported_formats()
coverages = wcs_capabilities_.list_coverages()
```

---

### 4. OpenAPIDoc
Una clase para interactuar con un documento OpenAPI y extraer información útil, como colecciones, rutas, parámetros y consultables, para diferentes tipos de APIs de OGC: coberturas, features o mapas.

#### Atributos
- `logger (logging.Logger)`: Una instancia de logger para registrar mensajes.
- `url (str)`: La URL de la especificación OpenAPI o del punto final de la colección OGC. Ejemplos incluyen:
- `spec (Dict)`: La especificación OpenAPI obtenida de la URL proporcionada.

#### Métodos
  - **`log(message: str, level: Optional[int] = logging.INFO) -> None`**: Registra un mensaje en el nivel de logging especificado si el logger está activo, de lo contrario, lo imprime en la consola.
  - **`_detect_api_type() -> Optional[str]`**: Detecta si la API es de Características, Coberturas o Mapas en función de las rutas.
  - **`fetch_openapi_spec() -> Optional[Dict]`**: Obtiene el documento OpenAPI de la URL especificada.
  - **`validate_spec() -> None`**: Valida la especificación OpenAPI utilizando openapi-spec-validator.
  - **`get_info() -> Dict`**: Recupera información general sobre la API del documento OpenAPI.
  - **`get_paths() -> Dict[str, Dict[str, Any]]`**: Recupera todas las rutas disponibles del documento OpenAPI.
  - **`get_collections() -> List[str]`**: Extrae colecciones disponibles de las rutas de la API.
  - **`get_operations() -> List[str]`**: Obtiene una lista de operaciones (rutas) disponibles del documento OpenAPI.
  - **`get_queryables() -> Dict[str, Dict[str, Dict]]`**: Recupera todos los parámetros consultables para cada operación del documento OpenAPI.
  - **`get_operation_queryables(operation: str) -> Optional[Dict[str, Dict]]`**: Obtiene parámetros consultables específicos para una operación dada.
  - **`get_parameters() -> Dict[str, Dict[str, Dict]]`**: Recupera todos los parámetros, incluidas las referencias resueltas, del documento OpenAPI.
  - **`resolve_parameter(param: Dict) -> Dict`**: Resuelve una definición de parámetro que puede incluir referencias.

#### Ejemplo
```python
openapi_doc = OpenAPIDoc(url='https://api-features.ign.es', name='IGN')
info = openapi_doc.get_info()
paths = openapi_doc.get_paths()
collections = openapi_doc.get_collections()
```