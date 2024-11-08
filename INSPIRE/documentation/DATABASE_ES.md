# Documentación del Módulo de Base de Datos

## Descripción general
El módulo `database.py` define una clase para gestionar e interactuar con bases de datos geográficas, en particular bases de datos PostgreSQL con la extensión PostGIS.

## Clases

### GeoDBManager
Esta clase proporciona varios métodos para conectar con una base de datos, gestionar tablas y manejar datos. Incluye funcionalidades como obtener información de los esquemas, verificar la existencia de tablas, renombrar tablas y comparar datos entre tablas.

La conexión se configura usando credenciales proporcionadas directamente a través del diccionario `config` o cargadas desde variables de entorno especificadas en un archivo `.env`.

Si no se proporcionan, las credenciales se cargarán desde el archivo `.env`. El formato del diccionario debe seguir esta estructura:

#### Atributos
  - `_cursor` (Optional[psycopg2_cursor]): El objeto cursor para ejecutar consultas en la base de datos. Por defecto es None.
  - `logger` (logging.Logger): Instancia de logger utilizada para registrar mensajes.

#### Métodos
  - `log(message: str, level: Optional[str])`: Registra un mensaje en el nivel de registro especificado. Si no hay un logger disponible, imprime el mensaje en la consola.
  - `connect(config: Optional[Dict[str, Any]])`: Establece una conexión a una base de datos PostgreSQL utilizando las credenciales proporcionadas en el diccionario `config` o desde las variables de entorno.
  - `get_schemas() -> Dict[str, List[str]]`: Recupera todos los esquemas y sus tablas desde la base de datos, devolviéndolos como un diccionario.
  - `table_exists(schema: str, table_name: str)`: Verifica si una tabla específica existe en un esquema dado.
  - `get_count(schema: str, table_name: str)`: Devuelve el número total de filas en una tabla especificada.
  - `rename_table(schema: str, old_table_name: str, new_table_name: str)`: Cambia el nombre de una tabla dentro de un esquema especificado.
  - `create_table_from_feature(table_name: str, feature: ogr.Feature)`: Crea una tabla en PostgreSQL basada en las propiedades de una característica OGR.
  - `ogr_to_postgres_type(ogr_type: int)`: Mapea los tipos de campo de OGR a tipos de PostgreSQL.
  - `add_feature_to_table(schema: str, table_name: str, feature: ogr.Feature)`: Añade una característica de una fuente de datos OGR a una tabla de PostgreSQL, creando la tabla si no existe.
  - `_add_row_to_table(table_name: str, columns: Dict[str, str], SRID: int)`: Inserta una fila en una tabla de PostgreSQL, manejando las geometrías WKT adecuadamente.
  - `is_wkt(column_value: str)`: Determina si una cadena dada representa una geometría Well-Known Text (WKT).
  - `get_table_data(table_name: str, columns: List[str], key_column: str)`: Recupera datos de una tabla PostgreSQL para fines de comparación.
  - `compare_tables(schema: str, table1: str, table2: str, column_mapping: Dict[str, str], key_column: str)`: Compara datos entre dos tablas de PostgreSQL e identifica filas añadidas, eliminadas y modificadas.
  - `_rollback()`: Revierte la transacción actual, deshaciendo todos los cambios no confirmados.
  - `_save_changes()`: Confirma la transacción actual, guardando todas las modificaciones en la base de datos.

#### Ejemplo
```python
schema = '00_Places'
table = 'spain'
database = GeoDBManager()
for feature in features:
    database.add_feature_to_table(schema, table_new, feature)
```