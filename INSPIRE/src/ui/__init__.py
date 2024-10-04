from datetime import datetime
import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import psycopg2

import pandas as pd
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QFormLayout, QLabel, QInputDialog, QDialog, 
    QDialogButtonBox, QTabWidget, QComboBox, QDateEdit, QMenuBar, QAction, QSpacerItem, 
    QSizePolicy, QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QDate, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from src.modules.inspire import WFSService, AtomService
from src.modules.database import GeoDBManager
from src.modules.loggers import Logger
from src.modules.reports import Document
from src.utils.utils import day_ranges, month_ranges

APP = QApplication(sys.argv)

# Define the schema globally
service_schema: Dict[str, Any] = {
    "service": {
        "url": "",
        "type": "WFS",
        "version": "2.0.0",
        "parameters": {
            "typeNames": "gn:NamedPlace",
            "srsName": "EPSG:4258"
        }
    },
    "database": {
        "schema": "",
        "table": ""
    }
}

mapping_schema: Dict[str, Any] = {
    'beginlifespanversion' : 'beginlifespanversion',
    'localid' : 'localid',
    'namespace' : 'namespace',
    'localisedcharacterstring' : 'localisedcharacterstring',
    'language' : 'language',
    'nativeness' : 'nativeness',
    'namestatus' : 'namestatus',
    'text' : 'text',
    'script' : 'script',
    'type' : 'type'
}

class KeyValueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add Key-Value")
        self.setMinimumSize(300, 150)

        # Layout for the dialog
        layout = QVBoxLayout(self)

        # Key input
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText("Enter key")
        layout.addWidget(QLabel("Key:"))
        layout.addWidget(self.key_input)

        # Value input
        self.value_input = QLineEdit(self)
        self.value_input.setPlaceholderText("Enter value")
        layout.addWidget(QLabel("Value:"))
        layout.addWidget(self.value_input)

        # Buttons: OK and Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Returns the key and value entered by the user."""
        return self.key_input.text(), self.value_input.text()

class JsonEditor(QWidget):
    """
    A widget for editing and managing JSON data in a tree-like structure, 
    with support for modifying regions, managing a schema, and handling database 
    connection details.

    This class provides an interface to:
        - Load and edit a JSON file, displaying its structure in a tree widget.
        - Add, edit, and delete regions of the JSON file according to a schema.
        - Modify the schema and propagate changes to the JSON structure.
        - Manage and save database connection details to a `.env` file.

    Attributes:
        json_file (str): Path to the JSON file that will be loaded and edited.
        schema_file (str): Path to the JSON schema file that defines the structure for adding new regions.
        data (Dict[str, Any]): Parsed content of the JSON file loaded into memory.
        tabs (QTabWidget): Tabbed interface holding both the JSON editor and database connection forms.
        tree (QTreeWidget): Widget to visualize and edit the JSON data in a hierarchical format.
        schema_layout (QVBoxLayout): Layout that holds dynamically generated forms based on the schema.
        add_button (QPushButton): Button to trigger the addition of a new region based on the schema.
        delete_button (QPushButton): Button to delete the currently selected region in the tree.
        modify_schema_button (QPushButton): Button to open a dialog for modifying the schema.
        host_field (QLineEdit): Input field for the database host.
        port_field (QLineEdit): Input field for the database port.
        database_field (QLineEdit): Input field for the database name.
        username_field (QLineEdit): Input field for the database username.
        password_field (QLineEdit): Input field for the database password.
        save_db_button (QPushButton): Button to save the database connection details to a `.env` file.

    Methods:
        load_json() -> Dict[str, Any]:
            Loads the specified JSON file and returns the parsed data.
        load_env() -> None:
            Loads the environment variables from a `.env` file and sets the database connection fields.
        populate_tree() -> None:
            Populates the tree widget with the current JSON data and expands all nodes.
        add_tree_items(data: Any, tree_item: QTreeWidgetItem) -> None:
            Recursively adds items to the tree based on JSON data (handles dicts and lists).
        open_add_item_form() -> None:
            Opens a form for adding a new region to the JSON file based on the schema.
        generate_form_fields(schema: Dict[str, Any], layout: QFormLayout, parent_keys: List[str]) -> None:
            Dynamically generates form input fields from the schema, supporting nested structures.
        clear_form_layout(layout: QFormLayout) -> None:
            Clears all input fields from the provided form layout.
        submit_new_data() -> None:
            Submits the new data entered in the form, updates the JSON structure, and refreshes the tree.
        cancel_addition() -> None:
            Cancels the addition of a new region and hides the input form.
        edit_item(item: QTreeWidgetItem) -> None:
            Opens an input dialog to edit the value of the selected tree item.
        update_data_from_tree(self, item: QTreeWidgetItem, schema: Dict[str, Any]) -> None:
            Recursively update the schema based on the tree contents.
        item_selected(item: QTreeWidgetItem) -> None:
            Enables the delete button if a top-level item (region) is selected.
        save_json() -> None:
            Saves the current state of the JSON data back to the original file.
        delete_item() -> None:
            Deletes the currently selected top-level region from the JSON data and tree.
        get_item_key_path(item: QTreeWidgetItem) -> List[str]:
            Returns the full key path of the selected tree item as a list of strings.
        set_nested_value(data: Dict[str, Any], key_path: List[str], value: str) -> None:
            Sets a value in a nested dictionary based on a list of keys representing the path.
        remove_nested_value(data: Dict[str, Any], key_path: List[str]) -> None:
            Recursively removes a key from a nested dictionary (JSON structure) based on the key path.
        reload_json() -> None:
            Reloads the JSON data from the file and refreshes the tree widget.
        update_json_based_on_schema(new_schema: Dict[str, Any]) -> None:
            Updates the JSON data based on a modified schema and saves the changes to the file.
        save_db_info() -> None:
            Saves the current database connection details to a `.env` file.
    """

    def __init__(self, json_file: str, is_mapping_file:Optional[bool] = False) -> None:
        """
        Initializes the JsonEditor widget.

        Parameters:
            json_file (str): The path to the JSON file to be edited.
            schema_file (str): The path to the JSON file to be used as a schema.
        """
        super().__init__()

        self.json_file = json_file
        self.is_mapping_file = is_mapping_file
        self.data = self.load_json()

        # Main layout
        self.layout = QVBoxLayout()

        # Create a tab widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Add JSON editor tab
        self.json_tab = QWidget()
        if is_mapping_file:        
            self.tabs.addTab(self.json_tab, "Table Mapping Editor")
        else:
            self.tabs.addTab(self.json_tab, "Service Editor")

        # JSON editor layout
        self.json_layout = QVBoxLayout(self.json_tab)

        # Tree widget to show JSON data
        self.tree = QTreeWidget()
        if self.is_mapping_file:
            self.tree.setHeaderLabels(["Old_column", "New_column"])
        else:
            self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.itemDoubleClicked.connect(self.edit_item)
        self.tree.itemClicked.connect(self.item_selected)  # Handle selection for delete
        self.json_layout.addWidget(self.tree)

        # Populate tree with initial data
        self.populate_tree()

        # Form to add new data based on the schema
        self.schema_layout = QVBoxLayout()
        self.schema_form = QFormLayout()
        self.schema_layout.addLayout(self.schema_form)

        # Add form buttons (Submit and Cancel)
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add New Region")
        self.add_button.clicked.connect(self.open_add_item_form)
        self.delete_button = QPushButton("Delete Selected Region")
        self.delete_button.setEnabled(False)  # Disabled initially, enabled on selection
        self.delete_button.clicked.connect(self.delete_item)

        self.json_layout.addLayout(self.schema_layout)
        self.json_layout.addWidget(self.add_button)
        self.json_layout.addWidget(self.delete_button)
        
        # Buttons to add and remove keys
        self.add_key_button = QPushButton("Add Key")
        self.add_key_button.clicked.connect(self.add_key)

        self.remove_key_button = QPushButton("Remove Key")
        self.remove_key_button.clicked.connect(self.remove_key)

        # Add buttons to layout
        self.json_layout.addWidget(self.add_key_button)
        self.json_layout.addWidget(self.remove_key_button)

        # Add Database connection tab
        if not is_mapping_file:
            self.db_tab = QWidget()
            self.tabs.addTab(self.db_tab, "Database Connection")

            # Database layout
            self.db_layout = QFormLayout(self.db_tab)

            # Create form fields for DB connection info
            self.host_field = QLineEdit()
            self.port_field = QLineEdit()
            self.database_field = QLineEdit()
            self.username_field = QLineEdit()
            self.password_field = QLineEdit()

            self.db_layout.addRow(QLabel("Host:"), self.host_field)
            self.db_layout.addRow(QLabel("Port:"), self.port_field)
            self.db_layout.addRow(QLabel("Database:"), self.database_field)
            self.db_layout.addRow(QLabel("Username:"), self.username_field)
            self.db_layout.addRow(QLabel("Password:"), self.password_field)

            self.save_db_button = QPushButton("Save")
            self.save_db_button.clicked.connect(self.save_db_info)
            self.db_layout.addWidget(self.save_db_button)

            # Load the .env file if it exists
            self.load_env()

        # Set the layout for the main window
        self.setLayout(self.layout)

        # Set window properties
        self.setWindowTitle("Project Configurations Editor")
        self.resize(900, 600)
    
    def load_json(self) -> Dict[str, Any]:
        """
        Load the JSON file and return the data as a dictionary.

        Returns:
            (Dict[str, Any]): The JSON data loaded from the file.
        """
        try:
            with open(self.json_file, 'r', encoding='UTF-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: The file '{self.json_file}' was not found.")
            return {}
        except json.JSONDecodeError:
            print("Error: The JSON file is not valid.")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {}

    def load_env(self) -> None:
        """
        Load the .env file and set the database connection fields if the file exists.
        """
        # Check if the .env file exists
        if os.path.exists('.env'):
            load_dotenv()  # Load environment variables from .env file

            # Set the form fields with values from .env
            self.host_field.setText(os.getenv('HOST', ''))
            self.port_field.setText(os.getenv('PORT', ''))
            self.database_field.setText(os.getenv('DATABASE', ''))
            self.username_field.setText(os.getenv('USERNAME', ''))
            self.password_field.setText(os.getenv('PASSWORD', ''))

    def populate_tree(self) -> None:
        """
        Populate the QTreeWidget with the JSON data and expand all nodes.
        """
        self.tree.clear()
        self.add_tree_items(self.data, self.tree.invisibleRootItem())
        self.tree.expandAll()  # Expand all nodes to make the whole tree visible

    def add_tree_items(self, data: Any, tree_item: QTreeWidgetItem) -> None:
        """
        Recursively add items to the tree from JSON data.

        Args:
            data (Any): The JSON data to add, which can be a dict, list, or any other type.
            tree_item (QTreeWidgetItem): The parent tree item to which the new items will be added.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                child = QTreeWidgetItem([key, ""])
                tree_item.addChild(child)
                self.add_tree_items(value, child)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                child = QTreeWidgetItem([f"Index {index}", ""])
                tree_item.addChild(child)
                self.add_tree_items(value, child)
        else:
            tree_item.setText(1, str(data))

    def open_add_item_form(self) -> None:
        """
        Open the form for adding new regions based on the imported schema.
        Clears existing form fields and prepares the UI for new input.
        """
        self.clear_form_layout(self.schema_form)  # Clear existing form fields
        self.region_name_field = QLineEdit()  # New region name
        self.schema_form.addRow("Region Name:", self.region_name_field)

        # Use the global schema to create the form
        if self.is_mapping_file:
            self.generate_form_fields(mapping_schema, self.schema_form, [])
        else:
            self.generate_form_fields(service_schema, self.schema_form, [])

        # Check if buttons already exist
        if not hasattr(self, 'submit_button'):
            # Submit and Cancel buttons
            self.submit_button = QPushButton("Save")
            self.cancel_button = QPushButton("Cancel")
            self.submit_button.clicked.connect(self.submit_new_data)
            self.cancel_button.clicked.connect(self.cancel_addition)

            self.button_layout.addWidget(self.submit_button)
            self.button_layout.addWidget(self.cancel_button)
            self.schema_layout.addLayout(self.button_layout)

        self.submit_button.show()  # Ensure buttons are shown
        self.cancel_button.show()  # Ensure buttons are shown    
    
    def generate_form_fields(self, schema: Dict[str, Any], layout: QFormLayout, parent_keys: List[str]) -> None:
        for key, value in schema.items():
            full_key_path = parent_keys + [key]
            if isinstance(value, dict):
                # Recursively generate fields for nested dictionaries
                layout.addRow(QLabel(f"{key}:"))
                self.generate_form_fields(value, layout, full_key_path)
            else:
                # Create input fields for primitive types (strings, etc.)
                input_field = QLineEdit(str(value))  # Pre-fill with default value
                input_field.setObjectName(".".join(full_key_path))  # Store the full key path as object name
                layout.addRow(key, input_field)
    
    def clear_form_layout(self, layout: QFormLayout) -> None:
        """
        Clear all the form fields from the specified layout.

        Args:
            layout (QFormLayout): The layout from which to clear fields.
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def submit_new_data(self) -> None:
        """
        Submit the new data entered in the form and update the JSON data.

        The new region is added to the JSON structure and the tree is refreshed.
        """
        region_name = self.region_name_field.text()
        if not region_name:
            # Handle the case where the region name is not provided
            return

        new_region_data = {}
        for i in range(self.schema_form.count()):
            item = self.schema_form.itemAt(i)
            if isinstance(item.widget(), QLineEdit) and item.widget() != self.region_name_field:
                key_path = item.widget().objectName().split(".")
                value = item.widget().text()
                self.set_nested_value(new_region_data, key_path, value=value)

        # Add new region to the main JSON
        self.data[region_name] = new_region_data

        # Save updated data
        self.save_json()

        # Update the tree display
        self.populate_tree()

        # Clear the form
        self.clear_form_layout(self.schema_form)

        # Hide the submit button and cancel button
        self.submit_button.hide()
        self.cancel_button.hide()

        # Optionally, clear the region name field
        self.region_name_field.clear()

    def cancel_addition(self) -> None:
        """
        Cancel the addition and hide the form.
        """
        # Clear the form and hide the buttons
        self.clear_form_layout(self.schema_form)
        self.submit_button.hide()
        self.cancel_button.hide()

    def add_key(self) -> None:
        """Add a new key to the selected item."""
        current_item = self.tree.currentItem()
        if current_item:
            dialog = KeyValueDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                # Get the entered key and value from the dialog
                new_key, new_value = dialog.get_data()
                # Ensure key is not empty
                if new_key:
                    # Add the new key-value pair to the tree
                    current_item.addChild(QTreeWidgetItem([new_key, str(new_value)]))
                    # Update the JSON data
                    key_path = self.get_item_key_path(current_item)
                    new_data = {new_key: new_value}
                    self.set_nested_value(self.data, key_path, value=new_data)

                    # Save the updated JSON
                    self.save_changes()
                else:
                    QMessageBox.warning(self, "Invalid Input", "Key cannot be empty.")
                    
    def remove_key(self) -> None:
        """Remove the selected key."""
        current_item = self.tree.currentItem()
        if current_item and current_item.parent():
            reply = QMessageBox.question(self, 'Remove Key',
                                        f"Are you sure you want to remove '{current_item.text(0)}'?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                if current_item and current_item.parent():
                    index = current_item.parent().indexOfChild(current_item)
                    current_item.parent().removeChild(current_item)
                    # Save the updated JSON
                    self.save_changes()
                else:
                    QMessageBox.warning(self, "Invalid Selection", "Please select a parameter to remove.")

    def save_changes(self) -> None:
        """Save changes made in the tree back to the schema."""
        self.data = {}
        self.update_data_from_tree(self.tree.invisibleRootItem(), self.data)
        self.save_json()
            
    def update_data_from_tree(self, item: QTreeWidgetItem, schema: Dict[str, Any]) -> None:
        """Recursively update the schema based on the tree contents."""
        for i in range(item.childCount()):
            child = item.child(i)
            key = child.text(0)
            if child.childCount() > 0:
                schema[key] = {}
                self.update_data_from_tree(child, schema[key])
            else:
                schema[key] = child.text(1)  # Update value

    def item_selected(self, item: QTreeWidgetItem) -> None:
        """
        Enable buttons to add or remove a (key, value) pair when an item is selected,
        and also enable the Delete button only for top-level regions.

        Parameters:
            item (QTreeWidgetItem): The selected tree item.
        """
        # Check if the selected item is a top-level item (i.e., has no parent)
        if item.parent() is None:
            self.delete_button.setEnabled(True)  # Enable delete button for top-level items
        else:
            self.delete_button.setEnabled(False)  # Disable delete button for non-top-level items
            
        self.add_key_button.setEnabled(True)
        self.remove_key_button.setEnabled(True)
    
    def save_json(self) -> None:
        """
        Save the current JSON data back to the file.

        This method writes the modified JSON data to the specified file in a pretty-printed format.
        """
        with open(self.json_file, 'w', encoding='UTF-8') as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def edit_item(self, item: QTreeWidgetItem, column:int) -> None:
        """
        Edit the selected item in the tree.

        Parameters:
            item (QTreeWidgetItem): The tree item to edit.
        """
        key = item.text(0)
        value = item.text(1)
        if self.is_mapping_file and column == 0:
            new_key, ok = QInputDialog.getText(self, "Edit key", f"Edit key '{key}':", QLineEdit.Normal, key)
            if ok and new_key:
                # Update the tree
                item.setText(0, new_key)
                # Update the underlying JSON data
                key_path = self.get_item_key_path(item)
                self.set_nested_value(self.data, key_path, prev_key=key)
        else:
            new_value, ok = QInputDialog.getText(self, "Edit Value", f"Edit value for '{key}':", QLineEdit.Normal, value)
            if ok and new_value:
                # Update the tree
                item.setText(1, new_value)

                # Update the underlying JSON data
                key_path = self.get_item_key_path(item)
                self.set_nested_value(self.data, key_path, value=new_value)

        # Save the updated JSON
        self.save_json()
        

    def delete_item(self) -> None:
        """
        Delete the selected region (top-level item) from the tree and JSON data.

        If the selected item is a top-level item, it will be removed from the data structure
        and the tree view will be updated accordingly.
        """
        selected_item = self.tree.currentItem()
        if selected_item and selected_item.parent() is None:
            region_name = selected_item.text(0)

            # Remove the region from the JSON data
            if region_name in self.data:
                del self.data[region_name]

                # Save the updated JSON data
                self.save_json()

                # Refresh the tree to reflect the changes
                self.populate_tree()

                # Disable the delete button after deletion
                self.delete_button.setEnabled(False)
                
    def get_item_key_path(self, item: QTreeWidgetItem) -> List[str]:
        """
        Get the full key path of a tree item.

        Parameters:
            item (QTreeWidgetItem): The tree item whose key path is to be determined.

        Returns:
            List[str]: A list of keys representing the path to the item in the JSON data.
        """
        key_path = []
        while item:
            key_path.insert(0, item.text(0))
            item = item.parent()
        return key_path

    def set_nested_value(self, data: Dict[str, Any], key_path: str, prev_key: Optional[str]=None, value: Optional[str]=None) -> None:
        """
        Set a value in a nested dictionary based on a dot-separated key path.

        Parameters:
            data (Dict[str, Any]): The dictionary to modify.
            key_path (str): The dot-separated string representing the path to the value.
            value (str): The value to set.
        """
        key = key_path[0]
        if len(key_path) > 1:
            if key not in data:
                if prev_key is None:
                    data[key] = {}
                else:
                    new_data = {}
                    for old_key, value in data.items():
                        if old_key == prev_key:
                            new_data[key] = data[old_key]  # Insert the new key with the old value
                        else:
                            new_data[old_key] = value  # Keep other keys unchanged
                    if new_data:
                        data.clear()
                        for k, v in new_data.items():
                            data[k] = v
            self.set_nested_value(data[key], key_path[1:], prev_key=prev_key, value=value)
        else:
            if prev_key is None:
                data[key] = value
            else:
                new_data = {}
                for old_key, value in data.items():
                    if old_key == prev_key:
                        new_data[key] = data[old_key]  # Insert the new key with the old value
                    else:
                        new_data[old_key] = value  # Keep other keys unchanged
                if new_data:
                    data.clear()
                    for k, v in new_data.items():
                        data[k] = v
            

    def remove_nested_value(self, data: Dict[str, Any], key_path: List[str]) -> None:
        """
        Recursively remove a key from the nested JSON structure.

        This method traverses the given nested dictionary (JSON structure) based on
        the provided key path and removes the specified key. If the key path consists
        of multiple keys, the method will navigate through the nested dictionaries
        until it reaches the final key, which it then removes.

        Parameters:
            data (Dict[str, Any]): The nested dictionary from which the key should be removed.
            key_path (List[str]): A list of keys representing the path to the key to be removed.
                                The first element is the top-level key, and each subsequent
                                element represents a deeper level in the nested structure.
        """
        key = key_path[0]
        if len(key_path) > 1:
            self.remove_nested_value(data[key], key_path[1:])
        else:
            del data[key]
            
    def reload_json(self) -> None:
        """Reload the JSON data and refresh the QTreeWidget."""
        self.data = self.load_json()  # Load the new JSON data
        self.populate_tree()  # Populate the tree with the updated data
    
    def update_json_based_on_schema(self, new_schema: dict) -> None:
        """
        Updates the `config.json` file by aligning the parameters for each region's 
        "service" section with a new schema. Parameters in the existing config are added, 
        updated, or removed to match the new schema.

        This method performs the following operations:
        - Loads the current `config.json` file.
        - Updates each region's "service" parameters to match the ones defined in 
        the `new_schema`.
        - Adds new parameters, updates existing ones, and removes parameters no 
        longer present in the new schema.
        - Optionally, the method can be extended to handle "database" updates 
        if needed.
        - Saves the updated configuration back to `config.json`.

        Args:
            new_schema (dict): The new schema that defines the structure and parameters 
                            for the "service" section, which contains the parameters 
                            to be added, updated, or removed.

        Raises:
            FileNotFoundError: Raised if `config.json` file is not found.
            json.JSONDecodeError: Raised if there's an error in reading `config.json`.
            Any other exceptions raised while saving the file are caught and printed.
        """
        # Load the existing config.json
        try:
            with open(self.json_file, 'r', encoding='UTF-8') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            print("config.json not found.")
            return
        except json.JSONDecodeError as e:
            print(f"Error reading config.json: {e}")
            return

        # Update each region's service and database with new schema parameters
        for region, data in config.items():
            # Update service parameters
            service = data.get("service", {})
            service_params = service.get("parameters", {})

            # Add or update parameters in the service
            for param, value in new_schema["service"]["parameters"].items():
                if param not in service_params:
                    service_params[param] = value  # Add new parameters
                else:
                    service_params[param] = value  # Update existing parameters

            # Remove parameters not present in the new schema
            for param in list(service_params.keys()):
                if param not in new_schema["service"]["parameters"]:
                    del service_params[param]

            service["parameters"] = service_params  # Update the service parameters
            data["service"] = service  # Update the config for this region

            # Optionally, you can also update database parameters if needed
            # You could add additional logic here if the database structure changes

        # Save the updated config back to config.json
        try:
            with open(self.json_file, 'w', encoding='UTF-8') as config_file:
                json.dump(config, config_file, ensure_ascii=False, indent=4)
            print("config.json updated successfully.")
        except Exception as e:
            print(f"Error saving config.json: {e}")
            
        self.reload_json()

    def save_db_info(self) -> None:
        """
        Save the DB connection info to a .env file.

        This method writes the current database connection information into a .env file
        which can be used to load environment variables later.
        """
        with open('.env', 'w', encoding='UTF-8') as env_file:
            env_file.write(f"HOST={self.host_field.text()}\n")
            env_file.write(f"PORT={self.port_field.text()}\n")
            env_file.write(f"DATABASE={self.database_field.text()}\n")
            env_file.write(f"USERNAME={self.username_field.text()}\n")
            env_file.write(f"PASSWORD={self.password_field.text()}\n")

class ConfigPathsDialog(QDialog):
    """
    A dialog window that displays configuration paths for services, schema, and database.

    This dialog uses a QTableWidget to display the configuration paths in a structured
    tabular format. The paths are presented in two columns: a description of the
    configuration and the corresponding file path.

    Users can double-click on any path in the table to open the file in its default
    application, provided the path is valid and the file exists.

    Attributes:
        paths_table (QTableWidget): A table widget displaying the description and path
                                    of each configuration file.
    
    Methods:
        open_file_from_path(row, column):
            Opens the file corresponding to the path in the selected table row if the 
            path column is double-clicked. The file is opened with the system's default 
            application, depending on the operating system (e.g., xdg-open for Linux, 
            os.startfile for Windows).
    """
    def __init__(self, services_config, mapping_info, database_config):
        super().__init__()
        
        self.setWindowTitle("Configuration Paths")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        # Create a QTableWidget
        self.paths_table = QTableWidget()
        self.paths_table.setRowCount(3)  # 3 rows for each configuration path
        self.paths_table.setColumnCount(2)  # 2 columns: Description and Path
        self.paths_table.setHorizontalHeaderLabels(["Description", "Path"])

        # Set configuration paths
        self.paths_table.setItem(0, 0, QTableWidgetItem("Services Config"))
        self.paths_table.setItem(0, 1, QTableWidgetItem(services_config))
        self.paths_table.setItem(1, 0, QTableWidgetItem("Table Mapping Info"))
        self.paths_table.setItem(1, 1, QTableWidgetItem(mapping_info))
        self.paths_table.setItem(2, 0, QTableWidgetItem("Database Config"))
        self.paths_table.setItem(2, 1, QTableWidgetItem(database_config))

        # Set read-only properties for table
        self.paths_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make it non-editable
        self.paths_table.resizeColumnsToContents()  # Adjust column widths to fit content
        
        # Connect double-click signal
        self.paths_table.cellDoubleClicked.connect(self.open_file_from_path)

        layout.addWidget(self.paths_table)
        self.setLayout(layout)
        
    def open_file_from_path(self, row, column):
        """
        Opens the file corresponding to the double-clicked path in the table.

        This method is triggered when the user double-clicks a cell in the table. 
        If the double-click occurs in the 'Path' column (column 1), the method attempts 
        to open the file at the specified path using the system's default application. 
        The method checks the current operating system to determine the appropriate
        method for opening the file.

        Notes:
        - On Linux and macOS, the file is opened with 'xdg-open'.
        - On Windows, the file is opened with 'os.startfile'.
        - If the file does not exist, a message is printed in the console.
        
        Parameters:
            row (int): The row index of the double-clicked cell.
            column (int): The column index of the double-clicked cell.
        
        Raises:
            Exception: If the file cannot be opened due to a system or path-related error.
        
        """
        if column == 1:  # Ensure the path column was clicked
            file_path = self.paths_table.item(row, 1).text()
            full_path = os.path.abspath(file_path)  # Convert to absolute path

            if os.path.exists(full_path):
                # Try to open the file using the system's default application
                try:
                    if os.name == 'posix':  # For Linux and MacOS
                        subprocess.run(['xdg-open', full_path], check=True)
                    elif os.name == 'nt':  # For Windows
                        os.startfile(full_path)
                except Exception as e:
                    print(f"Failed to open file: {e}")
            else:
                print("File does not exist:", full_path)

class Worker(QThread):
    # Signal to communicate with the main thread
    update_progress = pyqtSignal(str)
    
    def __init__(self, config_file:str, date_ranges: List[datetime], execute_btn:QPushButton, mapping_file:Optional[str] = None) -> None:
        super().__init__()
        self.config_file = config_file
        self.mapping_file = mapping_file
        self.date_ranges = date_ranges
        self.execute_btn = execute_btn

    def run(self):
        self.execute_btn.setEnabled(False)
        print("Execution started!")  # Implement your execution logic here
        
        inspire_log = Logger('src.modules.inspire', level='DEBUG', handlers=['console', 'file'])
        capabilities_log = Logger('src.modules.capabilities', level='DEBUG', handlers=['console', 'file'])
        database_log = Logger('src.modules.database', level='DEBUG', handlers=['console', 'file'])
        reports_log =  Logger('src.modules.reports', level='DEBUG', handlers=['console', 'file'])
        
        
        # Open the JSON file and read the data
        data = None
        mapping = None
        try:
            with open(self.config_file, 'r', encoding='UTF-8') as file:
                data = json.load(file)
            with open(self.mapping_file, 'r', encoding='UTF-8') as file:
                mapping = json.load(file)
        except:
            pass
        
        if data is not None:
            for region, info in data.items():
                url = info.get('service').get('url')
                parameters = info.get('service').get('parameters')
                
                schema = info.get('database').get('schema')
                table = info.get('database').get('table')
                table_new = info.get('database').get('table') + '_new'
                database = GeoDBManager()
                old_items = database.get_count(schema, table)
                
                today = f'{datetime.now().year}{datetime.now().month}{datetime.now().day}'
                report_name = f'Informe_{region}_{today}'
                report = Document(output_dir='reports', file_name=report_name)
                report.add_text(f'INFORME DE DESCARGA NOMENCLATOR<br/>{region}', 'Heading1')
                rows = []
                
                if info.get('service'):
                    if info.get('service').get('type') == 'WFS':
                        WFS = WFSService(source=url, name=region)
                        report.add_text('1. Descarga de datos mediante servicio Inspire', 'Heading2')
                        report.add_text("""Se han realizado peticiones en intervalos de un mes al servicio WFS Inspire de la Comunidad Autónoma, 
                                        cuyas capacidades se pueden consultar a través del siguiente enlace:""")
                        report.add_text(WFS.source + f"?service={WFS.service}&version={WFS.version}&request=GetCapabilities")
                        
                        for date_range in self.date_ranges:
                            begin = date_range[0].isoformat()
                            end = date_range[1].isoformat()
                            features = WFS.get_feature(SQL_PREDICATE=f"beginLifespanVersion >= '{begin}' and beginLifespanVersion < '{end}'", **parameters)
                            n = 0
                            for feature in features:
                                database.add_feature_to_table(schema, table_new, feature)
                                n += 1
                                self.update_progress.emit(f"{region} [{begin}/{end}]: \nInserting item {n}...")
                            rows.append({'Fecha inicio': begin, 'Fecha fin': end, 'Insertados': n})
                        self.update_progress.emit(f"{region}: \nAll items inserted, building report...")
                    elif info.get('service').get('type') == 'ATOM':
                        ATOM = AtomService(source=url, name=region)
                        report.add_text('1. Descarga de datos mediante servicio Inspire', 'Heading2')
                        report.add_text("""Se han realizado peticiones en intervalos de un mes al servicio ATOM Inspire de la Comunidad Autónoma:""")
                        report.add_text(ATOM.source)
                        
                        typeNames = parameters.get('typeNames')
                        if typeNames:
                            features = ATOM.get_feature(typeNames=typeNames)
                            n = 0
                            for feature in features:
                                database.add_feature_to_table(schema, table_new, feature)
                                n += 1
                                self.update_progress.emit(f"{region} [ATOM]: \nInserting item {n}...")
                            self.update_progress.emit(f"{region} [ATOM]: \nAll items inserted, building report...")
                
                if len(rows) > 0:
                    df = pd.DataFrame(rows)
                    df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
                    df['Año'] = df['Fecha inicio'].dt.year
                    grouped_df = df.groupby('Año')
                    for year in grouped_df:
                        year[1].drop('Año', axis=1, inplace=True)
                        report.add_table_from_df(f"Resumen de objetos geográficos extraídos mediante servicio de descarga.<br/>Año {year[0]}", year[1], 2, 1)
                
                report.add_text('A continuación, se muestra un resumen estadístico por años de los objetos geográficos descargados del servicio:')
                years = grouped_df['Insertados'].sum().reset_index()
                report.add_plot_from_df('Resumen estadístico.', years, 'Año', 'Insertados')
                report.add_text('2. Estado de la base de datos', 'Heading2')
                report.add_text(f"""Se ha realizado una conexión a la tabla "{schema}".{table} de la base
                                de datos Postgre <b>"NomenclatorGeograficoNacional"</b>, que ha devuelto un total de <b>{old_items}</b>
                                objetos geográficos.""")
                
                new_items = database.get_count(schema, table_new)
                print(f'Items in new table: {new_items}')
                report.add_text(f"""Se ha creado la tabla <b>"{schema}".{table_new}</b> para almacenar los resultados de la actualización,
                                insertándose un total de <b>{new_items}</b> objetos geográficos.""")
                report.save_pdf()
                
                if mapping is not None:
                    try:
                        report.add_text('3. Control de cambios', 'Heading2')
                        report.add_text(f'Se ha generado un reporte de control de cambios en formato Excel reports/{report_name}.xlsx')
                        added, removed, changed, changed_geometries = database.compare_tables(schema, table, table_new, mapping.get(region), 'localid')
                        database.export_summary_to_excel(added, removed, changed, changed_geometries, output_dir = 'reports', file_name = report_name)
                        
                    except psycopg2.errors.UndefinedColumn as e:
                        self.update_progress.emit(f"{region}: \n{e}")
                
                
        self.update_progress.emit(f"Execution completed")
        self.execute_btn.setEnabled(True)
        

class MainWindow(QWidget):
    """
    The main window of the application, providing a user interface to select a time period, 
    choose interval options, and access configuration editors.

    This window allows the user to set start and end dates, choose an interval type 
    (daily, monthly, or custom), and execute a specified action. The window also 
    includes a menu bar that enables users to open a configuration editor and 
    display a dialog showing the paths to configuration files.

    Attributes:
        services_config (str): The file path for the services configuration file.
        schema_info (str): The file path for the schema information file.
        database_config (str): The file path for the database configuration file.
        layout (QVBoxLayout): The main layout for arranging widgets vertically in the window.
        menu_bar (QMenuBar): The menu bar containing file-related options.
        file_menu (QMenu): The 'File' menu that houses actions such as opening the config editor.
        config_action (QAction): Action for opening the configuration editor.
        show_paths_action (QAction): Action for showing the configuration file paths.
        title_label (QLabel): A label displaying the form's title.
        form_layout (QFormLayout): Layout for the form fields such as date inputs and interval options.
        start_date_field (QDateEdit): Widget for selecting the start date.
        end_date_field (QDateEdit): Widget for selecting the end date.
        interval_combo (QComboBox): Dropdown for selecting the time interval type.
        custom_interval_label (QLabel): Label for the custom interval input.
        custom_interval_field (QSpinBox): Input field for custom interval in days.
        execute_button (QPushButton): Button to trigger the execution action.
        execute_button_layout (QHBoxLayout): Layout to position the Execute button.
    
    Constants:
        DAY_BY_DAY (str): Option for day-by-day interval processing.
        MONTH_BY_MONTH (str): Option for month-by-month interval processing.
        CUSTOM_INTERVAL (str): Option for custom interval processing.
    """
    DAY_BY_DAY = "Daily"
    MONTH_BY_MONTH = "Monthly"
    CUSTOM_INTERVAL = "Custom Interval"
    
    def __init__(self, services_config:Optional[str] = None, schema_info: Optional[str] = None, database_config:Optional[str] = None, table_mapping:Optional[str] = None):
        """
        Initializes the MainWindow and sets up the user interface components.

        This constructor configures the main layout of the window, including the form for 
        selecting start and end dates, choosing an interval type, and a button to execute 
        actions. It also sets up a menu with actions to open the configuration editor 
        and display paths to key configuration files.

        Parameters:
            services_config (Optional[str]): The path to the services configuration file. Defaults to 'config.json'.
            schema_info (Optional[str]): The path to the schema information file. Defaults to 'schema.json'.
            database_config (Optional[str]): The path to the database configuration file. Defaults to '.env'.

        Raises:
            FileNotFoundError: If any of the provided paths do not exist.
        """
        super().__init__()
        self.services_config = Path(services_config).resolve().as_posix() if (services_config is not None and os.path.exists(services_config)) else Path('config.json').resolve().as_posix()
        self.schema_info = Path(schema_info).resolve().as_posix() if (schema_info is not None and os.path.exists(schema_info)) else Path('schema.json').resolve().as_posix()
        self.database_config = Path(database_config).resolve().as_posix() if (database_config is not None and os.path.exists(database_config)) else Path('.env').resolve().as_posix()
        self.table_mapping = Path(table_mapping).resolve().as_posix() if (table_mapping is not None and os.path.exists(table_mapping)) else Path('mapping.json').resolve().as_posix()

        if not os.path.exists(self.services_config):
            raise FileNotFoundError(f"The services config file does not exist: {self.services_config}")
        
        # Set up the user interface
        self.setup_ui()
        self.show()
        sys.exit(APP.exec_())

    def setup_ui(self):
        """
        Sets up the user interface components, including the form, menu bar, and buttons.

        This method configures the layout for the start and end date fields, interval selection, 
        and the execute button. It also establishes the menu bar with options for 
        opening the configuration editor and showing configuration paths.
        """
        # Main layout for the window
        self.layout = QVBoxLayout()

        # Create a menu bar
        self.menu_bar = QMenuBar(self)

        # Add "File" menu
        self.file_menu = self.menu_bar.addMenu("File")

        # Create actions for the menu
        self.config_action = QAction("Open Configuration Editor", self)
        self.config_action.triggered.connect(self.open_config_editor)
        self.file_menu.addAction(self.config_action)
        
        self.mapping_action = QAction("Open Mapping Editor", self)
        self.mapping_action.triggered.connect(self.open_mapping_editor)
        self.file_menu.addAction(self.mapping_action)
        
        self.show_paths_action = QAction("Show Configuration Paths", self)
        self.show_paths_action.triggered.connect(self.show_config_paths)
        self.file_menu.addAction(self.show_paths_action)

        # Add the menu bar to the layout
        self.layout.setMenuBar(self.menu_bar)

        # Title label for the form
        self.title_label = QLabel("Time Period to Process")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")  # Optional styling
        self.layout.addWidget(self.title_label)

        # Form layout for date intervals
        self.form_layout = QFormLayout()

        # Start date field
        self.start_date_field = QDateEdit()
        self.start_date_field.setDate(QDate(2004, 1, 1))
        self.form_layout.addRow(QLabel("Start Date:"), self.start_date_field)

        # End date field
        self.end_date_field = QDateEdit()
        self.end_date_field.setDate(QDate.currentDate())
        self.form_layout.addRow(QLabel("End Date:"), self.end_date_field)

        # Interval selection
        self.interval_combo = QComboBox()
        self.interval_combo.addItems([self.DAY_BY_DAY, self.MONTH_BY_MONTH, self.CUSTOM_INTERVAL])
        self.interval_combo.setCurrentIndex(1)
        self.form_layout.addRow(QLabel("Select Interval:"), self.interval_combo)
        

        # Custom interval label and field (using QSpinBox for integer input)
        self.custom_interval_label = QLabel("Days:")
        self.custom_interval_label.setVisible(False)  # Initially hidden
        self.custom_interval_field = QSpinBox()  # Changed to QSpinBox
        self.custom_interval_field.setVisible(False)  # Initially hidden
        self.custom_interval_field.setMinimum(1)  # Set minimum value to 1
        self.custom_interval_field.setMaximum(365)  # Set maximum value to 365 for example

        # Add custom interval row but hide it initially
        self.form_layout.addRow(self.custom_interval_label, self.custom_interval_field)

        # Connect the combo box change event to toggle the custom interval field
        self.interval_combo.currentIndexChanged.connect(self.toggle_custom_interval_field)

        # Add form layout to the main layout
        self.layout.addLayout(self.form_layout)
        
        # Create a checkbox for generating a change control report
        self.change_control_checkbox = QCheckBox("Generate Change Control Report")
        self.change_control_checkbox.setChecked(False)  # Default unchecked
        self.layout.addWidget(self.change_control_checkbox)  # Add checkbox to the layout

        # Create a button layout for the Execute button
        self.execute_button_layout = QHBoxLayout()
        self.execute_button = QPushButton("Execute")
        self.execute_button.setIcon(QIcon.fromTheme("media-playback-start"))  # Set play icon
        self.execute_button.setToolTip("Start the process")
        self.execute_button.clicked.connect(self.execute_action_method)
        self.execute_button_layout.addStretch()  # Add stretchable space to push button right
        self.execute_button_layout.addWidget(self.execute_button)

        # Add the button layout to the main layout
        self.layout.addLayout(self.execute_button_layout)
        
        # Add a status label
        self.status_label = QLabel("Press the button to start the process.")
        self.layout.addWidget(self.status_label)

        # Add a spacer to keep the form at the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        # Set the main window layout
        self.setLayout(self.layout)

        # Set window properties
        self.setWindowTitle("IGN-CNIG INSPIRE SYNC")
        self.resize(400, 300)
        
    def show_config_paths(self) -> None:
        """
        Opens a dialog window that displays the paths to configuration files.

        This method launches a modal dialog (`ConfigPathsDialog`) that shows 
        the file paths for services configuration, schema information, and 
        database configuration. The paths are non-editable but viewable by the user.
        """
        config_dialog = ConfigPathsDialog(self.services_config, self.table_mapping, '.env')
        config_dialog.exec_()  # Show dialog modally

    def toggle_custom_interval_field(self) -> None:
        """
        Toggles the visibility of the custom interval input field based on the selected option.

        If the "Custom Interval" option is selected from the interval combo box, the custom 
        interval input field becomes visible, allowing users to input a custom interval in days.
        If a different option is selected, the custom interval field is hidden and its value is cleared.
        """
        if self.interval_combo.currentText() == self.CUSTOM_INTERVAL:
            self.custom_interval_label.setVisible(True)  # Show the label
            self.custom_interval_field.setVisible(True)  # Show the input field
        else:
            self.custom_interval_label.setVisible(False)  # Hide the label
            self.custom_interval_field.setVisible(False)  # Hide the input field
            self.custom_interval_field.clear()  # Clear input when hiding

    def open_config_editor(self) -> None:
        """
        Open the JSON editor window when the button is clicked.

        This method creates an instance of the JsonEditor class and shows the 
        editor window, allowing the user to modify the configuration settings.
        """
        self.editor = JsonEditor(json_file=self.services_config)
        self.editor.show()  # Show the JSON editor window
    
    def open_mapping_editor(self) -> None:
            """
            Open the JSON editor window when the button is clicked.

            This method creates an instance of the JsonEditor class and shows the 
            editor window, allowing the user to modify the mapping settings to
            compare two versions of the table.
            """
            self.editor = JsonEditor(json_file=self.table_mapping, is_mapping_file=True)
            self.editor.show()  # Show the JSON editor window

    def execute_action_method(self) -> None:
        """
        Placeholder method for Execute action.

        This method is triggered when the Execute button is clicked. It currently
        prints a message to the console. Implement your execution logic in this method
        to process the selected time period based on the form inputs.
        """
        if self.start_date_field.date() > self.end_date_field.date():
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before the end date.")
            return
        ranges = []
        if self.interval_combo.currentText() == self.DAY_BY_DAY:
            ranges = day_ranges(self.start_date_field.text(), self.end_date_field.text())
        elif self.interval_combo.currentText() == self.CUSTOM_INTERVAL:
            n = self.custom_interval_field
            ranges = day_ranges(self.start_date_field, self.end_date_field, n)
        elif self.interval_combo.currentText() == self.MONTH_BY_MONTH:
            ranges = month_ranges(self.start_date_field.text(), self.end_date_field.text())
        # Worker thread
        if self.change_control_checkbox.isChecked():
            self.worker = Worker(config_file=self.services_config, mapping_file=self.table_mapping, date_ranges=list(ranges), execute_btn=self.execute_button)
        else:
            self.worker = Worker(config_file=self.services_config, date_ranges=list(ranges), execute_btn=self.execute_button)
            
        self.worker.update_progress.connect(self.update_status)
        self.status_label.setText("Process started...")
        self.worker.start()  # Start the worker thread
    
    def update_status(self, message):
        self.status_label.setText(message)
        
