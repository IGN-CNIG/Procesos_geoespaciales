# Database Module Documentation

## Overview
The `database.py` module defines a class to manage and interact with geographical databases, particularly PostgreSQL databases with PostGIS extension.

## Classes

### GeoDBManager
This class provides various methods to connect to a database, manage tables, and handle data. It includes functionalities such as fetching schema information, checking table existence, renaming tables, and comparing data between tables.

The connection is configured using credentials either provided directly through the `config` dictionary or loaded from environment variables specified in a `.env` file.

If not provided, the credentials will be loaded from the `.env` file. The dictionary format should follow this structure:

``` python
config = {
    'HOST': 'XX.XX.XX.XX',         # The IP address or hostname of the database server
    'PORT': 'XXXX',                # The port number of the database service
    'DATABASE': 'DatabaseName',    # The name of the database
    'USERNAME': 'user',            # The database user
    'PASSWORD': 'pwd'              # The password for the database user
}
```

#### Attributes
  - `_cursor` (Optional[psycopg2_cursor]): The cursor object for executing database queries. Defaults to None.
  - `logger` (logging.Logger): Logger instance used for logging messages.

#### Methods
  - **`log(message: str, level: Optional[str])`**: Logs a message at the specified logging level. If no logger is available, prints the message to the console.
  - **`connect(config: Optional[Dict[str, Any]])`**: Establishes a connection to a PostgreSQL database using credentials provided in the `config` dictionary or from environment variables.
  - **`get_schemas() -> Dict[str, List[str]]`**: Retrieves all schemas and their tables from the database, returning them as a dictionary.
  - **`table_exists(schema: str, table_name: str)`**: Checks whether a specific table exists in a given schema.
  - **`get_count(schema: str, table_name: str)`**: Returns the total number of rows in a specified table.
  - **`rename_table(schema: str, old_table_name: str, new_table_name: str)`**: Renames a table within a specified schema.
  - **`create_table_from_feature(table_name: str, feature: ogr.Feature)`**: Creates a PostgreSQL table based on the properties of an OGR feature.
  - **`ogr_to_postgres_type(ogr_type: int)`**: Maps OGR field types to PostgreSQL types.
  - **`add_feature_to_table(schema: str, table_name: str, feature: ogr.Feature)`**: Adds a feature from an OGR data source to a PostgreSQL table, creating the table if it does not exist.
  - **`_add_row_to_table(table_name: str, columns: Dict[str, str], SRID: int)`**: Inserts a row into a PostgreSQL table, handling WKT geometries appropriately.
  - **`is_wkt(column_value: str)`**: Determines if a given string represents a Well-Known Text (WKT) geometry.
  - **`get_table_data(table_name: str, columns: List[str], key_column: str)`**: Retrieves data from a PostgreSQL table for comparison purposes.
  - **`compare_tables(schema: str, table1: str, table2: str, column_mapping: Dict[str, str], key_column: str)`**: Compares data between two PostgreSQL tables and identifies added, removed, and changed rows.
  - **`_rollback()`**: Rolls back the current transaction, undoing all uncommitted changes.
  - **`_save_changes()`**: Commits the current transaction, saving all modifications to the database.

#### Example
```python
schema = '00_Places'
table = 'spain'
database = GeoDBManager()
for feature in features:
    database.add_feature_to_table(schema, table_new, feature)
```