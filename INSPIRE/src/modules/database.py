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
import copy
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from dotenv import load_dotenv, dotenv_values
from osgeo import ogr
import pandas as pd
import psycopg2
from schema import Schema, And, Use, SchemaError


DB_CONFIG_SCHEMA = Schema({
    'host': And(Use(str)),
    'port': And(Use(int)),
    'database': And(Use(str)),
    'username': And(Use(str)),
    'password': And(Use(str)),
})

class GeoDBManager:
    """
    A class to manage and interact with geographical databases, particularly PostgreSQL databases with PostGIS extension.

    This class provides various methods to connect to a database, manage tables, and handle data. It includes functionalities
    such as fetching schema information, checking table existence, renaming tables, and comparing data between tables.

    Attributes:
        _cursor (Optional[psycopg2_cursor]): The cursor object for executing database queries. Defaults to None.
        logger (logging.Logger): Logger instance used for logging messages.

    ## Methods
        log(message: str, level: Optional[str] = logging.INFO) -> None:
            Logs a message at the specified logging level. If no logger is available, prints the message to the console.
        connect(config: Optional[Dict[str, Any]] = None) -> None:
            Establishes a connection to a PostgreSQL database using credentials provided in the `config` dictionary or from environment variables.
        get_schemas() -> Dict[str, List[str]]:
            Retrieves all schemas and their tables from the database, returning them as a dictionary.
        table_exists(schema: str, table_name: str) -> bool:
            Checks whether a specific table exists in a given schema.
        get_count(schema: str, table_name: str) -> int:
            Returns the total number of rows in a specified table.
        rename_table(schema: str, old_table_name: str, new_table_name: str) -> None:
            Renames a table within a specified schema.
        create_table_from_feature(table_name: str, feature: ogr.Feature) -> bool:
            Creates a PostgreSQL table based on the properties of an OGR feature.
        ogr_to_postgres_type(ogr_type: int) -> str:
            Maps OGR field types to PostgreSQL types.
        add_feature_to_table(schema: str, table_name: str, feature: ogr.Feature) -> None:
            Adds a feature from an OGR data source to a PostgreSQL table, creating the table if it does not exist.
        _add_row_to_table(table_name: str, columns: Dict[str, str], SRID: int) -> None:
            Inserts a row into a PostgreSQL table, handling WKT geometries appropriately.
        is_wkt(column_value: str) -> bool:
            Determines if a given string represents a Well-Known Text (WKT) geometry.
        get_table_data(table_name: str, columns: List[str], key_column: str) -> List[Dict[str, str]]:
            Retrieves data from a PostgreSQL table for comparison purposes.
        get_geom_column_name(self, schema: str, table: str) -> Optional[str]:
            Retrieve the name of the geometry column from a specified table in the database schema.
        compare_geometries(self, schema:str, table1:str, table2:str) -> Dict[str, Dict[str, str]]:
            Compare geometries between two tables in a specified schema.
        compare_tables(schema: str, table1: str, table2: str, column_mapping: Dict[str, str], key_column: str) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
            Compares data between two PostgreSQL tables and identifies added, removed, and changed rows.
        _rollback() -> None:
            Rolls back the current transaction, undoing all uncommitted changes.
        _save_changes() -> None:
            Commits the current transaction, saving all modifications to the database.
    """
    _cursor:psycopg2.extensions.cursor | None = None
    logger:logging.Logger = logging.getLogger(__name__)  # Obtain a logger for this module/class
    schemas: Dict
    
    def __init__(self, db_config:Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the GeoDBManager class by setting up the database connection based on provided configuration.

        Parameters:
            db_config (Optional[Dict[str, Any]]): A dictionary containing database connection details. 
                                                  If not provided, environment variables will be used.
        
        Raises:
            SchemaError: If the provided database configuration fails schema validation.
            Exception: For any other errors during initialization, such as connection issues.
        """
        try:
            if db_config is not None:
                if DB_CONFIG_SCHEMA.validate(db_config):
                    self.log("Database configuration is valid, establishing connection.", logging.INFO)
                    self.connect(db_config)
                    self.get_schemas()
            else:
                self.connect()
                self.log("Connected using environment variables.", logging.INFO)
                self.get_schemas()
        except SchemaError as se:
            self.log(f"Schema validation error: {se}", logging.ERROR)
            raise
        except Exception as e:
            self.log(f"Error during initialization: {e}", logging.ERROR)
            raise
            
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

    @classmethod
    def connect(cls, config:Optional[Dict[str, Any]] = None) -> None:
        """
        Establishes a connection to a PostgreSQL database.

        The connection is configured using credentials either provided directly through the `config` dictionary or 
        loaded from environment variables specified in a `.env` file.
        
        Side Effects:
            - Establishes a connection to the database and initializes the cursor for executing queries.

        Parameters:
            config (Optional[Dict[str, Any]]): A dictionary containing database connection details. If not provided, 
                                            the method will load credentials from the `.env` file.
                                            The dictionary format should follow this structure:
                                            
                config = {
                    'HOST': 'XX.XX.XX.XX',         # The IP address or hostname of the database server
                    'PORT': 'XXXX',                # The port number of the database service
                    'DATABASE': 'DatabaseName',    # The name of the database
                    'USERNAME': 'user',            # The database user
                    'PASSWORD': 'pwd'              # The password for the database user
                }

        Behavior:
            - If `config` is not provided, the method attempts to load the database credentials from environment 
            variables using the `dotenv_values()` function, which reads from a `.env` file.
            - A connection to the PostgreSQL database is established using the `psycopg2` library.
            - The database cursor is created and stored as an instance attribute (`self._cursor`) for future database interactions.

        Raises:
            psycopg2.OperationalError: If there is an error while attempting to connect to the database (e.g., invalid credentials or network issues).

        Example:
            >>> db_service.connect({
            ...     'HOST': '127.0.0.1',
            ...     'PORT': '5432',
            ...     'DATABASE': 'mydb',
            ...     'USERNAME': 'user',
            ...     'PASSWORD': 'pwd'
            ... })
        """
        if not config:
            load_dotenv()
            config = dotenv_values()
        if isinstance(config, dict):
            try:
                connection = psycopg2.connect(
                    host=config.get('HOST'),
                    port=config.get('PORT'),
                    database=config.get('DATABASE'),
                    user=config.get('USERNAME'),
                    password=config.get('PASSWORD')
                )
                cls._cursor = connection.cursor()
                GeoDBManager.log("Database connection established successfully.", logging.INFO)
            except psycopg2.OperationalError as e:
                GeoDBManager.log(f"Database connection failed: {e}", logging.ERROR)
                raise

    def get_schemas(self) -> None:
        """
        Get all the schemas and tables from each schema contained in the database in the form of a dict and 
        stores the retrieved schemas and tables in the `self.schemas` attribute.
        
        This method executes SQL queries to gather information from the `INFORMATION_SCHEMA.TABLES` 
        to list all schemas and the tables they contain. The result is a dictionary where each schema 
        is a key, and the associated value is a list of tables within that schema.
        """
        if self._cursor:
            tables = {}
            query = "SELECT DISTINCT table_schema FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
            self._cursor.execute(query)
            schemas = self._cursor.fetchall()
            for schema in schemas:
                query = f"SELECT table_name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' and table_schema='{schema[0]}'"
                self._cursor.execute(query)
                tables[schema[0]] = [table_name[0] for table_name in self._cursor.fetchall()]
            self.log(f"Retrieved schemas and tables: {tables}", logging.DEBUG)
            self.schemas = tables
            return
        else:
            self.log("No database cursor available.", logging.WARNING)
        self.schemas = {}
    
    def table_exists(self, schema:str, table_name:str) -> bool:
        """
        Checks whether a table exists in a specified schema.

        This method looks through the available schemas and checks if the provided schema contains the specified table.

        Parameters:
            schema (str): The name of the schema to check.
            table_name (str): The name of the table to check within the schema.

        Returns:
            bool: 
                - `True` if the specified table exists in the given schema.
                - `False` if the schema or the table does not exist.
        
        Example:
            >>> db_service.table_exists('public', 'users')
            True
        """
        if self._cursor:
            if schema in self.schemas:
                return table_name in self.schemas[schema]
        else:
            self.log("No database cursor available.", logging.WARNING)
        return False

    def get_count(self, schema:str, table_name:str) -> int:
        """
        Get the total number of rows in the specified table of the DB
        Parameters:
            table_name (str): Name of the table in the DB

        Returns:
            int: The total number of rows in the specified table. If the table does not exist or 
                    another error occurs, this method will raise an exception.
        """
        if self._cursor:
            if self.table_exists(schema, table_name):
                table_name = f'"{schema}".{table_name}'
                query = f'SELECT COUNT(*) FROM {table_name}'
                self._cursor.execute(query)
                return self._cursor.fetchone()[0]
        else:
            self.log("No database cursor available.", logging.WARNING)
        
        return 0
    
    def rename_table(self, schema:str, old_table_name: str, new_table_name: str) -> None:
        """
        Rename a table in PostgreSQL within the specified schema.

        This method executes an SQL command to rename a table from `old_table_name` to `new_table_name`
        in the provided schema. It commits the change if successful or rolls back in case of an error.
        
        Notes:
        
        - The table names are enclosed in double quotes to handle cases where table names might 
        include special characters or reserved words.
        - Ensure that the new table name does not conflict with existing table names in the schema.
        - If an exception occurs, an error message is printed and the transaction is rolled back.

        Parameters:
            schema (str): The schema in which the table resides. This is used to fully qualify the table name.
            old_table_name (str): The current name of the table to be renamed.
            new_table_name (str): The new name for the table.
        
        Returns:
            bool: Returns `True` if the table was renamed successfully. Returns `False` if there was an error 
                    during the renaming process.
        
        Example:
            >>> rename_table(schema='public', old_table_name='old_table', new_table_name='new_table')
            True
        """
        if self._cursor:
            if self.table_exists(schema, old_table_name):
                old_table_name = f'"{schema}".{old_table_name}'
                rename_sql = f"ALTER TABLE {old_table_name} RENAME TO {new_table_name};"

                try:
                    self._cursor.execute(rename_sql)
                    self._save_changes()
                    self.log(f"Table '{old_table_name}' renamed to '{new_table_name}' successfully.")
                    self.get_schemas()
                    return True
                except Exception as e:
                    self.log(f"The table coud not be renamed.\n{e.pgerror}", logging.ERROR)
                    self.rollback()
        else:
            self.log("No database cursor available.", logging.WARNING)
        
        return False

    def create_table_from_feature(self, table_name: str, feature: ogr.Feature) -> bool:
        """
        Creates a PostgreSQL table based on the properties (fields) of an OGR feature.
        
        Parameters:
            feature (ogr.Feature): The OGR feature to extract the schema from.
            table_name (str): The name of the table to be created in PostgreSQL.
            
        Returns:
            bool: Returns True if the table was created successfully. Returns False if there was an error during the renaming process.
        """
        if self._cursor:
            # Start constructing the CREATE TABLE statement
            create_table_sql = f"CREATE TABLE {table_name} (\n"

            # Loop through each field in the feature and extract its name and type
            for index in range(feature.GetFieldCount()):
                field_defn = feature.GetFieldDefnRef(index)
                field_name = field_defn.GetName().split('|')[0]
                field_type = self.ogr_to_postgres_type(field_defn.GetType())

                # Add the column definition to the CREATE TABLE statement
                create_table_sql += f"    {field_name} {field_type},\n"

            # Add a geometry column (assuming WKT geometry is stored in a 'geom' field)
            create_table_sql += "    geom GEOMETRY\n"

            # Close the statement
            create_table_sql += ");"

            # Execute the CREATE TABLE statement using psycopg2
            try:
                self._cursor.execute(create_table_sql)
                self.log(f'The table {table_name} has been successfully created.')
                self._save_changes()
                self.get_schemas()
                return True
            except Exception as e:
                self.log(f'The table {table_name} could not be created:\n{e.pgerror}', logging.ERROR)
                self._rollback()
        else:
            self.log("No database cursor available.", logging.WARNING)
        
        return False
    
    @staticmethod
    def ogr_to_postgres_type(ogr_type):
        """
        Maps OGR field types to PostgreSQL types.
        
        Parameters:
            ogr_type (int): The OGR field type (as returned by GetFieldDefnRef().GetType()).

        Returns:
            str: Corresponding PostgreSQL data type as a string.
        """
        type_mapping = {
            ogr.OFTString: 'TEXT',
            ogr.OFTInteger: 'INTEGER',
            ogr.OFTReal: 'DOUBLE PRECISION',
            ogr.OFTDate: 'DATE',
            ogr.OFTTime: 'TIME',
            ogr.OFTDateTime: 'TIMESTAMP',
            ogr.OFTInteger64: 'BIGINT',
        }
        return type_mapping.get(ogr_type, 'TEXT')  # Default to TEXT if the type is not mapped

    def add_feature_to_table(self, schema:str, table_name:str , feature:ogr.Feature) -> None:
        """
        Add a feature from an OGR data source to a PostgreSQL table, creating the table if it does not exist.

        This method checks whether the specified schema and table exist in the PostgreSQL database. If the table does
        not exist, it creates the table based on the feature's schema. It then processes the feature's fields and 
        inserts the feature's properties, handling multi-value fields if present.
        
        Notes:
        - The method checks for the existence of the schema and table. If the table doesn't exist, 
        it calls `create_table_from_feature` to create it.
        - Handles multi-value fields (e.g., strings like '(2:Latn,Latn)') by inserting multiple rows, 
        one for each value in the multi-value field.
        - The geometry is exported as WKT (Well-Known Text) and inserted as a column named 'geom'.
        - The method assumes that the feature's geometry has a spatial reference system (SRS) defined, 
        and extracts the EPSG code to set the `SRID` in the insert operation.

        Parameters:
            schema (str): The schema where the table resides. If the schema or table doesn't exist, the table will be created.
            table_name (str): The name of the table to which the feature will be added.
            feature (ogr.Feature): The feature to be inserted into the table. The feature's geometry and properties will be extracted and inserted as rows in the table.

        Raises:
            psycopg2.Error: Raised if there is any issue with the PostgreSQL query execution, such as connection issues 
                or malformed queries.
        
        Example:
            >>> feature = ogr_feature_from_somewhere()  # Get the OGR feature
            >>> self.add_feature_to_table(schema='public', table_name='places', feature=feature)
        """
        if self._cursor:
            if not self.table_exists(schema, table_name):
                if self.create_table_from_feature(f'"{schema}".{table_name}', feature):
                    self.log(f"Table '{table_name}' created successfully in schema '{schema}'.")
                    
            epsg_code = int(feature.GetDefnRef().GetGeomFieldDefn(0).srs.GetAttrValue('AUTHORITY', 1)) if feature.GetDefnRef().GetGeomFieldDefn(0) else None
            
            multivalue_fields = {}
            count = 0
            for index in range(feature.GetFieldCount()):
                # Get field name and value
                field_name = feature.GetFieldDefnRef(index).GetName()
                field_value = feature.GetField(index)
                
                # Check if the field has multiple values
                if isinstance(field_value, str):
                    # Check for a pattern like "(n:value1,value2,...)" indicating multiple values
                    if field_value.startswith('(') and ':' in field_value:
                        # This looks like it could be a multi-value field (e.g., '(2:Latn,Latn)')
                        _, values = field_value.strip('()').split(':', 1)
                        values = values.split(',')
                        if len(values) > 0:
                            count = len(values)
                        multivalue_fields[field_name] = values
                if isinstance(field_value, list):
                    if len(field_value) > 0:
                        count = len(field_value)
                    multivalue_fields[field_name] = field_value
                
            # Extract properties and geometry from the feature
            properties = json.loads(feature.ExportToJson()).get('properties')
            properties['geom'] = feature.geometry().ExportToWkt()
            
            # Handle multi-value fields by inserting multiple rows
            if count > 0:
                for index in range(count):
                    properties_copy = copy.deepcopy(properties)
                    for field_name, field_values in multivalue_fields.items():
                        try:
                            properties_copy[field_name] = field_values[index]
                        except IndexError:
                            properties_copy[field_name] = None
                    self._add_row_to_table(table_name=f'"{schema}".{table_name}', columns=properties_copy, SRID=epsg_code)
            else:
                self._add_row_to_table(table_name=f'"{schema}".{table_name}', columns=properties, SRID=epsg_code)
                
        else:
            self.log("No database cursor available.", logging.WARNING)
                
    def _add_row_to_table(self, table_name:str, columns: Dict[str, str], SRID:int):
        """
        Insert a row into a PostgreSQL table, converting geometries in WKT format to the correct spatial representation.

        This method constructs an SQL `INSERT` query to add a row to the specified table. It processes each column 
        in the input dictionary `columns`, checking if the value represents a WKT geometry. If a column contains 
        WKT geometry, it is converted using `ST_GeomFromText`. Non-geometry string values are escaped and single-quoted.

        Parameters:
            table_name (str): The name of the table to insert the row into.
            columns (Dict[str, str]): A dictionary of column names and their corresponding values to be inserted.
            SRID (int): The spatial reference ID (SRID) for the geometry.
            
        Raises:
            psycopg2.Error: Raised if there is any issue with the PostgreSQL query execution, such as connection issues 
                or malformed queries.
        """
        for key, value in columns.items():
            if isinstance(value, str):
                if self.is_wkt(value):
                    columns[key] = f"ST_GeomFromText('{value}', {SRID})"
                else:
                    value = value.replace("'", "\'\'") # quotes in the string need to be double so it doesn't interrupt the query
                    columns[key] = f"'{value}'" # string values need to be single quoted

        str_columns = ', '.join(map(str, columns.values()))
        str_columns = str_columns.replace("None", "null")
        query = f'INSERT INTO {table_name} VALUES({str_columns})'
        self.log(f'Executing query: {query}', logging.DEBUG)
        try:
            self._cursor.execute(query)
            if self._cursor.statusmessage != 'INSERT 0 1':
                self.log(f'Row could not be inserted into table {table_name}.', logging.WARNING)
            self._save_changes()
        except Exception as e:
            self.log(f'Error during insertion of row into table {table_name}.', logging.ERROR)
            self.log(e, logging.ERROR)
            
    @staticmethod
    def is_wkt(column_value: str) -> bool:
        """
        Determines whether a given string represents a Well-Known Text (WKT) geometry.

        This function checks if the input string (`column_value`) starts with one of the common WKT 
        geometry types such as 'POINT', 'LINESTRING', 'POLYGON', etc. If the string matches one of 
        these types, the function returns `True`, indicating that the column value is likely a WKT 
        geometry.
        
        WKT Geometry Types Checked:
        --------------------------
        - POINT
        - LINESTRING
        - POLYGON
        - MULTIPOINT
        - MULTILINESTRING
        - MULTIPOLYGON
        - GEOMETRYCOLLECTION

        Parameters:
            column_value (str): The string value to be checked for WKT geometry formatting.
        
        Returns:
            bool: Returns `True` if the input string represents a WKT geometry; `False` otherwise.
        """
        # List of common geometry type keywords that WKT starts with
        wkt_geometry_types = ['POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION']
            
        # Check if the field value starts with any known WKT geometry type
        if any(column_value.startswith(geom_type) for geom_type in wkt_geometry_types):
            return True

        return False  # No WKT column found

    def get_table_data(self, table_name:str, columns:List[str], key_column:str) -> Dict[str, Dict[str, str]]:
        """
        Retrieve data from a PostgreSQL table for comparison purposes.

        Parameters:
            table_name (str): The name of the table from which data will be retrieved.
            columns (List[str]): A list of column names to be retrieved from the table.
            key_column (str): The primary key column to identify rows uniquely.

        Returns:
            (Dict[str, Dict[str, str]]): A dictionary where each key is a value from the key_column and each value is a 
                dictionary of column names and their corresponding values for that key.

        Raises:
            psycopg2.Error: Raised if there is any issue with the PostgreSQL query execution, such as connection issues 
                or malformed queries.
        """
        columns = ', '.join(columns)
        query = f'SELECT {key_column}, {columns} FROM {table_name}'
        self._cursor.execute(query)
        
        # Fetch column names from the cursor description
        column_names = [desc[0] for desc in self._cursor.description]
        
        # Fetch all rows from the query
        rows = self._cursor.fetchall()
        
        # Create a list of dictionaries with column names as keys
        result = {}
        for row in rows:
            key_value = row[0]  # The value of the key_column
            value_dict = dict(zip(column_names[1:], row[1:]))  # Skip the first element which is the key_column
            result[key_value] = value_dict
        return result
    
    @classmethod
    def get_geom_column_name(cls, schema: str, table: str) -> Optional[str]:
        """
        Retrieve the name of the geometry column from a specified table in the database schema.

        This method queries the PostGIS `geometry_columns` metadata table to identify the geometry column 
        in the specified table within the given schema. It returns the schema name, table name, and 
        geometry column name if found.

        Parameters:
            schema (str): The schema in which the table resides (e.g., '01_Andalucia').
            table (str): The name of the table to query for geometry column information (e.g., 'and_inspire').

        Returns:
            Optional[str]: The name of the geometry column. Returns `None` if no geometry column is found in the table.

        Raises:
            psycopg2.Error: If there is an error executing the SQL query (e.g., invalid schema or table).

        Example:
        >>> schema = "01_Andalucia"
        >>> table = "and_inspire"
        >>> get_geom_column_name(schema, table)
        'geom'
        """
        if cls._cursor:
            query = """SELECT f_geometry_column
                        FROM geometry_columns
                        WHERE f_table_schema = %s
                        AND f_table_name = %s"""
            
            # Execute the query
            cls._cursor.execute(query, (schema, table))
            
            # Fetch the first result
            result = cls._cursor.fetchone()
            
            if result:
                return result[0]
            
        return None
    
    def compare_geometries(self, schema:str, table1:str, table2:str) -> Dict[str, Dict[str, str]]:
        """
        Compare geometries between two tables in a specified schema.

        This method retrieves the geometry columns from the specified tables and 
        performs a SQL query to compare the geometries based on their local IDs. 
        It returns a dictionary where each key is a local ID, and the value is 
        another dictionary containing the previous and new geometries as well as 
        a boolean indicating whether the geometries are equal.

        Parameters
        ----------
        schema : str
            The schema in which the tables reside (e.g., '01_Andalucia').
        table1 : str
            The name of the first table to compare (e.g., 'and_inspire_v1').
        table2 : str
            The name of the second table to compare (e.g., 'and_inspire_v2').

        Returns
        -------
        dict[str, dict[str, str]]
            A dictionary where each key is the local ID and the value is another 
            dictionary containing:
            - 'prev_geom' (str): The previous geometry as WKT (Well-Known Text).
            - 'new_geom' (str): The new geometry as WKT.
            - 'geometries_equal' (bool): A boolean indicating whether the geometries are equal.

            Returns an empty dictionary if no differences are found or if geometry 
            columns are not found in the specified tables.

        Raises
        ------
        psycopg2.Error
            If there is an error executing the SQL query (e.g., invalid schema, table names, or geometry column issues).

        Example
        -------
        >>> schema = "01_Andalucia"
        >>> table1 = "and_inspire_v1"
        >>> table2 = "and_inspire_v2"
        >>> compare_geometries(schema, table1, table2)
        {'localid_value_1': {'prev_geom': 'POINT(1 1)', 'new_geom': 'POINT(1 2)', 'geometries_equal': False},
        'localid_value_2': {'prev_geom': 'LINESTRING(0 0, 1 1)', 'new_geom': 'LINESTRING(0 0, 1 2)', 'geometries_equal': False}}
        """
        geom_compare = []
        if self._cursor:
            table1_geom_col = self.get_geom_column_name(schema, table1)
            table2_geom_col = self.get_geom_column_name(schema, table2)
            if table1_geom_col and table2_geom_col:
                # SQL query to compare geometries
                query = f"""SELECT a.localid, ST_AsText(a.geom) AS prev_geom, ST_AsText(b.geom) AS new_geom, ST_Equals(a.geom, b.geom) AS geometries_equal
                    FROM "{schema}".{table1} a
                    JOIN "{schema}".{table2} b
                    ON a.localid = b.localid
                    WHERE NOT ST_Equals(a.geom, b.geom);"""

                # Execute the query
                self._cursor.execute(query)
                
                # Fetch column names from the cursor description
                column_names = [desc[0] for desc in self._cursor.description]

                # Fetch and print the results
                # Create a list of dictionaries with column names as keys
                for row in self._cursor.fetchall():
                    value_dict = dict(zip(column_names, row))
                    geom_compare.append(value_dict)
        
        return geom_compare


    
    def compare_tables(self, schema:str, table1:str, table2:str, column_mapping:Dict[str, str], key_column:str) -> Tuple[List[Tuple], List[Tuple], List[Tuple], List[Tuple]]:
        """
        Compare data between two PostgreSQL tables and identify added, removed, and changed rows.

        Parameters:
            schema (str): The schema where the tables reside.
            table1 (str): The name of the first table.
            table2 (str): The name of the second table.
            column_mapping (Dict[str, str]): A mapping of columns from `table1` to corresponding columns in `table2`.
            key_column (str): The primary key column used to uniquely identify rows in both tables.

        Returns:
            (Tuple[List[Tuple], List[Tuple], List[Tuple], List[Tuple]]): Three lists of tuples representing added rows, removed rows, and changed rows, respectively.

        Raises:
            psycopg2.Error: Raised if there is any issue with the PostgreSQL query execution, such as connection issues 
                or malformed queries.

        Example:
            >>> column_mapping = {'name': 'place_name', 'geom': 'location_geom'}
            >>> added, removed, changed, changed_geometries = self.compare_tables('01_Places', 'places_old', 'places_new', column_mapping, 'id')
        """
        added = []
        removed = []
        changed = []
        changed_geometries = self.compare_geometries(schema, table1, table2)
        
        
        if self._cursor and self.table_exists(schema, table1) and self.table_exists(schema, table2):
            
            try:
                table1_data = self.get_table_data(f'"{schema}".{table1}', column_mapping.keys(), key_column)
                table2_data = self.get_table_data(f'"{schema}".{table2}', column_mapping.values(), key_column)
            except:
                raise
            
            for key, table2_values in table2_data.items():
                if key not in table1_data.keys():
                    added.append((key, table2_values))
                else:
                    table1_values = table1_data[key]
                    changes = {}
                    for col1, col2 in column_mapping.items():
                        if table1_values[col1] != table2_values[col2]:
                            changes[f'{col1} ({table1}) -> {col2} ({table2})'] = {
                                'old': table1_values[col1],
                                'new': table2_values[col2]
                            }
                    if changes:
                        changed.append((key, changes))
            
            for key, values in table1_data.items():
                if key not in table2_data.keys():
                    removed.append((key, values))
                    
        else:
            self.log("No database cursor available.", logging.WARNING)
                
        return added, removed, changed, changed_geometries
    
    def generate_summary(self, added: List[Tuple[str, Dict[str, str]]],
                            removed: List[Tuple[str, Dict[str, str]]],
                            changed: List[Tuple[str, Dict[str, Dict[str, str]]]]) -> str:
        """
        Generate a string summary of added, removed, and changed rows.
        
        Parameters:
            added (List[Tuple[str, Dict[str, str]]]): List of added rows. Each tuple contains key and corresponding values.
            removed (List[Tuple[str, Dict[str, str]]]): List of removed rows. Each tuple contains key and corresponding values.
            changed (List[Tuple[str, Dict[str, Dict[str, str]]]]): List of changed rows. Each tuple contains key and a 
                dictionary of changes (with old and new values).
        
        Returns:
            str: A formatted string summarizing the added, removed, and changed rows.
        """
        summary = []
        
        # Added rows
        if added:
            summary.append("Added Items:\n")
            for key, values in added:
                summary.append(f"  - gml_id: {key}\n    Values: {values}\n")
        else:
            summary.append("No items were added.\n")
        
        # Removed rows
        if removed:
            summary.append("Removed Items:\n")
            for key, values in removed:
                summary.append(f"  - gml_id: {key}\n    Values: {values}\n")
        else:
            summary.append("No items were removed.\n")
        
        # Changed rows
        if changed:
            summary.append("Changed Items:\n")
            for key, changes in changed:
                summary.append(f"  - gml_id: {key}\n")
                for column, change in changes.items():
                    summary.append(f"    - {column}: {change['old']} -> {change['new']}\n")
        else:
            summary.append("No items were changed.\n")
        
        return "\n".join(summary)
    
    def export_summary_to_excel(self, added: List[Tuple[str, Dict[str, str]]],
                              removed: List[Tuple[str, Dict[str, str]]],
                              changed: List[Tuple[str, Dict[str, Dict[str, str]]]],
                              changed_geometries: List[Tuple[str, Dict[str, Dict[str, str]]]],
                              output_dir: str, file_name:str):
        """
        Generate pandas DataFrames from added, removed, and changed rows, and export them to an Excel file.

        Parameters:
            added (List[Tuple[str, Dict[str, str]]]): List of added rows. Each tuple contains key and corresponding values.
            removed (List[Tuple[str, Dict[str, str]]]): List of removed rows. Each tuple contains key and corresponding values.
            changed (List[Tuple[str, Dict[str, Dict[str, str]]]]): List of changed rows. Each tuple contains key and a 
                dictionary of changes (with old and new values).
            file_path (str): The path where the Excel file will be saved.
        
        Returns:
            None
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # Convert the added rows to a DataFrame
        if added:
            added_df = pd.DataFrame([{'gml_id': key, **values} for key, values in added])
        else:
            added_df = pd.DataFrame(columns=['gml_id'] + list(added[0][1].keys()) if added else [])

        # Convert the removed rows to a DataFrame
        if removed:
            removed_df = pd.DataFrame([{'gml_id': key, **values} for key, values in removed])
        else:
            removed_df = pd.DataFrame(columns=['gml_id'] + list(removed[0][1].keys()) if removed else [])

        # Convert the changed rows to a DataFrame
        if changed:
            changed_data = []
            for key, changes in changed:
                for column, change in changes.items():
                    changed_data.append({'gml_id': key, 'Column': column, 'Old Value': change['old'], 'New Value': change['new']})
            changed_df = pd.DataFrame(changed_data)
        else:
            changed_df = pd.DataFrame(columns=['gml_id', 'Column', 'Old Value', 'New Value'])
            
        if changed_geometries:
            changed_geometries_df = pd.DataFrame(changed_geometries)
        else:
            changed_geometries_df = pd.DataFrame(columns=['localid', 'Old Geometry', 'New Geometry'])

        # Save each DataFrame to an Excel file with separate sheets
        with pd.ExcelWriter(f'{output_dir}/{file_name}.xlsx') as writer:
            added_df.to_excel(writer, sheet_name='Added Items', index=False)
            removed_df.to_excel(writer, sheet_name='Removed Items', index=False)
            changed_df.to_excel(writer, sheet_name='Changed Items', index=False)
            changed_geometries_df.to_excel(writer, sheet_name='Changed Geometries', index=False)

        print(f"Added, removed, and changed items exported to Excel at {file_name}.xlsx")
        

    def _rollback(self) -> None:
        """
        Roll back the current transaction.

        This method rolls back (reverts) all uncommitted changes made in the current transaction. 
        It undoes any modifications executed by the cursor since the last commit or rollback.

        Use this method if an error occurs during a transaction, or if you need to revert changes 
        that have not yet been committed to the database.

        Raises:
            psycopg2.Error: Raised if there is an issue with the rollback operation, such as a connection issue or 
                failure in the transaction control.
        """
        self._cursor.connection.rollback()
        self.log('Changes have been dropped.', logging.DEBUG)
    
    def _save_changes(self) -> None:
        """
        Commit the current transaction.

        This method commits all changes made during the current transaction to the database. 
        After calling this method, the modifications executed by the cursor will be permanently 
        saved to the database.

        Use this method after successfully executing a series of database operations to ensure 
        that the changes are stored in the database.

        Raises:
            psycopg2.Error: Raised if there is an issue with the commit operation, such as a connection issue 
                or failure in the transaction control.
        """
        self._cursor.connection.commit()
        self.log('Changes have been commited to DB.', logging.DEBUG)
        
    @property
    def cursor(self):
        return self._cursor
    
    @property
    def items(self):
        return self.items