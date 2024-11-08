import json
import os
import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QComboBox, QLabel, QMessageBox, QTabWidget, 
                            QTextEdit, QGridLayout, QFileDialog, QGroupBox, QCheckBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, pyqtSignal, QThread, Qt
from PyQt5.QtGui import QKeySequence, QFont


from main import main_process
from dotenv import load_dotenv


MIN_IMAGE_VALUE = -32768
MAX_IMAGE_VALUE = 32767

class MapWindow(QMainWindow):
    # Define a signal to pass selected features to the parent window
    selected_tiles_signal = pyqtSignal(list) # Sending the list of tiles
    map_loaded_signal = pyqtSignal()
    map_closed_signal = pyqtSignal(str)  # Sending region name
    
    def __init__(self, selected_tiles=None, region_name=None, parent=None):
        super().__init__(parent)
        self.selected_tiles = selected_tiles or []
        self.region_name = region_name  # Store the region name for later use
        
        self.setWindowTitle(f"Select Tiles for {region_name}")
        self.setGeometry(100, 100, 800, 600)

        # Create a QWebEngineView to display the OpenLayers map
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # Load the local HTML file
        html_file_path = os.path.abspath("map.html")  # Update with your file path
        if os.path.exists(html_file_path):
            self.browser.page().loadFinished.connect(self.on_map_load)
            self.browser.setUrl(QUrl.fromLocalFile(html_file_path))
        else:
            QMessageBox.warning(self, "Error", f"{html_file_path} does not exist.")

        # Create a button to save selected features
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.saveSelectedFeatures)  # Connect button click to function
        # Set initial button geometry
        self.update_button_geometry()
        
    def resizeEvent(self, event):
        # Update the button geometry on resize
        self.update_button_geometry()
        super().resizeEvent(event)  # Call the base class implementation

    def update_button_geometry(self):
        # Set the button geometry with fixed width of 300 pixels and center it
        button_width = 300
        self.save_button.setGeometry((self.width() - button_width) // 2, self.height() - 50, button_width, 40)  # Centered at the bottom
        
    @pyqtSlot(bool)
    def on_map_load(self):
        # JavaScript code to highlight the tiles
        if self.selected_tiles:
            tiles_js = ",".join([f"'{tile}'" for tile in self.selected_tiles])
            self.browser.page().runJavaScript(f'selectTilesOnMap([{tiles_js}]);')
            self.map_loaded_signal.emit()
            

    def saveSelectedFeatures(self):
        # Execute JavaScript to call the function defined in HTML to get selected features
        self.browser.page().runJavaScript('getSelectedFeatures()', self.process_selected_tiles)

    @pyqtSlot(str)
    def process_selected_tiles(self, data):
        # Process the selected features received from JavaScript
        if data:
            selected_tiles = [item['Name'] for item in data]
            print("Selected Features:", selected_tiles)
            # Emit the signal to pass the selected features to the parent window
            self.selected_tiles_signal.emit(selected_tiles)
            # Emit the signal to open the enhancement window
            self.map_closed_signal.emit(self.region_name)
            # Close the MapWindow after emitting the signals
            self.close()
        else:
            QMessageBox.warning(self, "Error", "No features selected.")
            
            
class RegionInputWindow(QWidget):
    region_added_signal = pyqtSignal(str, dict)

    def __init__(self, region_name, enhancement_data):
        super().__init__()
        self.setWindowTitle(f"Region: {region_name}")
        self.setGeometry(150, 150, 820, 340)
        
        self.region_name = region_name  # Store the passed region name
        self.enhancement_data = enhancement_data

        layout = QVBoxLayout()

        # Create a table for seasonal data
        seasons = ['Spring', 'Summer', 'Autumn', 'Winter']
        columns = ['Season', 'RGB Min', 'RGB Max', 'NirGB Min', 'NirGB Max']
        self.season_table = QTableWidget()  # 4 rows (seasons) and 5 columns
        self.season_table.setRowCount(len(seasons))
        self.season_table.setColumnCount(len(columns))
        self.season_table.setHorizontalHeaderLabels(columns)
        
        # Populate the table with season names
        for i, season in enumerate(seasons):
            season_cell = QTableWidgetItem(season)
            season_cell.setFlags(season_cell.flags() & ~Qt.ItemIsEditable)
            self.season_table.setItem(i, 0, season_cell)
            if enhancement_data.get(season):
                rgb_min = enhancement_data[season]['RGB']['min'] or 0
                rgb_max = enhancement_data[season]['RGB']['max'] or 0
                nirgb_min = enhancement_data[season]['NirGB']['min'] or 0
                nirgb_max = enhancement_data[season]['NirGB']['max'] or 0
                self.season_table.setItem(i, 1, QTableWidgetItem(str(rgb_min)))
                self.season_table.setItem(i, 2, QTableWidgetItem(str(rgb_max)))
                self.season_table.setItem(i, 3, QTableWidgetItem(str(nirgb_min)))
                self.season_table.setItem(i, 4, QTableWidgetItem(str(nirgb_max)))
            
        
        layout.addWidget(self.season_table)

        self.add_enhancement_button = QPushButton("Save")
        self.add_enhancement_button.clicked.connect(self.add_enhancement)
        layout.addWidget(self.add_enhancement_button)

        self.setLayout(layout)

    def add_enhancement(self):
        try:
            # Create a data structure for seasonal data
            enhancement_data = {}
            for row in range(self.season_table.rowCount()):
                season = self.season_table.item(row, 0).text()
                # Safely get values from the table, defaulting to 0 if empty
                rgb_min = int(self.season_table.item(row, 1).text()) if self.season_table.item(row, 1) else MIN_IMAGE_VALUE
                rgb_max = int(self.season_table.item(row, 2).text()) if self.season_table.item(row, 2) else MAX_IMAGE_VALUE
                nirgb_min = int(self.season_table.item(row, 3).text()) if self.season_table.item(row, 3) else MIN_IMAGE_VALUE
                nirgb_max = int(self.season_table.item(row, 4).text()) if self.season_table.item(row, 4) else MAX_IMAGE_VALUE

                enhancement_data[season] = {
                    'RGB': {'min': rgb_min, 'max': rgb_max},
                    'NirGB': {'min': nirgb_min, 'max': nirgb_max}
                }

            # Emit signal to parent with new region data
            self.region_added_signal.emit(self.region_name, enhancement_data)

            self.close()  # Close the input window

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid integer values for RGB and NirGB.")
            
            
class ProjectWindow(QMainWindow):
    worker = None
    
    def __init__(self):
        super().__init__()
        self.current_project_path = None  # Store the current project directory path
        self.current_project_name = None  # Store the current project name

        self.setWindowTitle("Sentinel 2 Image Processing")
        self.setGeometry(100, 100, 800, 600)

        # Main layout (vertical layout to hold label, tab widget, and save button)
        main_layout = QVBoxLayout()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(main_layout)

        # Project Label on top
        self.project_name_label = QLabel("Project: No project")
        self.project_name_label.setStyleSheet("font-size: 12px; font-weight: bold;")  # Optional style

        # Main Tab Widget
        self.main_tab_widget = QTabWidget()
        
        # Create the different tabs
        self.main_tab_widget.addTab(self.create_project_settings_tab(), "Project Settings")
        self.main_tab_widget.addTab(self.create_credentials_tab(), "Credentials")
        self.main_tab_widget.addTab(self.create_email_tab(), "Email")
        

        # Add widgets to the main layout
        main_layout.addWidget(self.project_name_label)  # Top label
        main_layout.addWidget(self.main_tab_widget)  # Tabs in the middle
        
        # Save button at the bottom
        self.status_label = QLabel("Press the 'Execute' button to start the process.")
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_project)  # Connect button click to function
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self.execute_process)  # Connect button click to function
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.status_label)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.execute_button)
        
        main_layout.addLayout(buttons_layout)  # Save button at the bottom
        
        # Add menu bar
        self.create_menu_bar()
        
        self.regions = {}
        
    def create_credentials_tab(self):
        credentials_group = QGroupBox("Credentials")
        credentials_layout = QGridLayout()
        credentials_group.setLayout(credentials_layout)

        credentials_layout.addWidget(QLabel("Copernicus Data Space URL:"), 0, 0)
        copernicus_link = QLabel('<a href="https://dataspace.copernicus.eu/">https://dataspace.copernicus.eu/</a>')
        copernicus_link.setOpenExternalLinks(True)
        credentials_layout.addWidget(copernicus_link, 0, 1)
        
        credentials_layout.addWidget(QLabel("OPENEO_AUTH_CLIENT_ID:"), 1, 0)
        self.client_id_input = QLineEdit()
        credentials_layout.addWidget(self.client_id_input, 1, 1)

        credentials_layout.addWidget(QLabel("OPENEO_AUTH_CLIENT_SECRET:"), 2, 0)
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        credentials_layout.addWidget(self.client_secret_input, 2, 1)

        credentials_layout.addWidget(QLabel("OPENEO_AUTH_PROVIDER_ID:"), 3, 0)
        self.provider_id_input = QLineEdit()
        credentials_layout.addWidget(self.provider_id_input, 3, 1)

        
        s3_credentials_group = QGroupBox("S3 Credentials")
        s3_credentials_layout = QGridLayout()
        s3_credentials_group.setLayout(s3_credentials_layout)

        s3_credentials_layout.addWidget(QLabel("S3 Credentials URL:"), 0, 0)
        s3_link = QLabel('<a href="https://documentation.dataspace.copernicus.eu/APIs/S3.html">https://documentation.dataspace.copernicus.eu/APIs/S3.html</a>')
        s3_link.setOpenExternalLinks(True)
        s3_credentials_layout.addWidget(s3_link, 0, 1)

        s3_credentials_layout.addWidget(QLabel("AWS_ACCESS_KEY_ID:"), 1, 0)
        self.aws_access_key_input = QLineEdit()
        s3_credentials_layout.addWidget(self.aws_access_key_input, 1, 1)

        s3_credentials_layout.addWidget(QLabel("AWS_SECRET_ACCESS_KEY:"), 2, 0)
        self.aws_secret_access_key_input = QLineEdit()
        self.aws_secret_access_key_input.setEchoMode(QLineEdit.Password)
        s3_credentials_layout.addWidget(self.aws_secret_access_key_input, 2, 1)

        s3_credentials_layout.addWidget(QLabel("TOKEN_USERNAME:"), 3, 0)
        self.token_username_input = QLineEdit()
        s3_credentials_layout.addWidget(self.token_username_input, 3, 1)

        s3_credentials_layout.addWidget(QLabel("TOKEN_PASSWORD:"), 4, 0)
        self.token_password_input = QLineEdit()
        self.token_password_input.setEchoMode(QLineEdit.Password)
        s3_credentials_layout.addWidget(self.token_password_input, 4, 1)

        credentials_tab = QWidget()
        credentials_layout_tab = QVBoxLayout(credentials_tab)
        credentials_layout_tab.addWidget(credentials_group)
        credentials_layout_tab.addWidget(s3_credentials_group)
        credentials_layout_tab.addStretch()
        return credentials_tab
        
    def create_email_tab(self):
        # Adding the checkbox to the email settings tab
        self.send_notification_checkbox = QCheckBox("Send notification email")
        
        email_group = QGroupBox("Email Settings")
        email_layout = QGridLayout()
        email_group.setLayout(email_layout)

        email_layout.addWidget(QLabel("SMTP HOST:"), 0, 0)
        self.smtp_host_input = QLineEdit()
        email_layout.addWidget(self.smtp_host_input, 0, 1)

        email_layout.addWidget(QLabel("SMTP PORT:"), 1, 0)
        self.smtp_port_input = QLineEdit()
        email_layout.addWidget(self.smtp_port_input, 1, 1)

        email_layout.addWidget(QLabel("From:"), 2, 0)
        self.from_input = QLineEdit()
        email_layout.addWidget(self.from_input, 2, 1)

        email_layout.addWidget(QLabel("To:"), 3, 0)
        self.to_input = QTextEdit()
        email_layout.addWidget(self.to_input, 3, 1)

        email_layout.addWidget(QLabel("Subject:"), 4, 0)
        self.subject_input = QLineEdit()
        email_layout.addWidget(self.subject_input, 4, 1)

        email_tab = QWidget()
        email_layout_tab = QVBoxLayout(email_tab)
        email_layout_tab.addWidget(self.send_notification_checkbox)
        email_layout_tab.addWidget(email_group)
        email_layout_tab.addStretch()
        return email_tab

    def create_project_settings_tab(self):        
        project_settings_group = QGroupBox("Project Settings")
        vertical_layout = QVBoxLayout()
        project_settings_layout = QGridLayout()
        vertical_layout.addLayout(project_settings_layout)
        project_settings_group.setLayout(vertical_layout)

        project_settings_layout.addWidget(QLabel("Download directory:"), 1, 0)
        self.service_dir_input = QLineEdit()
        project_settings_layout.addWidget(self.service_dir_input, 1, 1)

        project_settings_layout.addWidget(QLabel("Number of threads:"), 2, 0)
        self.threads_input = QLineEdit()
        project_settings_layout.addWidget(self.threads_input, 2, 1)
        vertical_layout.addStretch()
        
        
        image_settings_group = QGroupBox("Image Settings")
        image_layout = QVBoxLayout()
        image_settings_group.setLayout(image_layout)
        image_settings_layout = QGridLayout()
        image_layout.addLayout(image_settings_layout)
        image_layout.addStretch()
        
        image_settings_layout.addWidget(QLabel("CRS (EPSG):"), 0, 0)
        self.crs_input = QLineEdit()
        image_settings_layout.addWidget(self.crs_input, 0, 1)

        image_settings_layout.addWidget(QLabel("Max cloud cover:"), 1, 0)
        self.max_cloud_cover_input = QLineEdit()
        image_settings_layout.addWidget(self.max_cloud_cover_input, 1, 1)

        image_settings_layout.addWidget(QLabel("Days offset:"), 2, 0)
        self.days_offset_input = QLineEdit()
        image_settings_layout.addWidget(self.days_offset_input, 2, 1)
        
        
        image_settings_layout.addWidget(QLabel("Download only:"), 3, 0)
        checkbox_layout = QHBoxLayout()
        self.only_complete = QCheckBox('Complete')
        self.only_latest = QCheckBox('Latest')
        checkbox_layout.addWidget(self.only_complete)
        checkbox_layout.addWidget(self.only_latest)
        checkbox_layout.addStretch()
        image_settings_layout.addLayout(checkbox_layout, 3, 1)
        
        ##########################################################################
        regions_group = QGroupBox("Image Treatment Regions")
        layout = QVBoxLayout(regions_group)

        new_region_layout = QHBoxLayout()
        self.region_input = QLineEdit()
        self.region_input.setPlaceholderText("Enter region name")
        new_region_layout.addWidget(self.region_input)

        self.add_region_button = QPushButton("Add Region")
        self.add_region_button.clicked.connect(self.add_region)
        new_region_layout.addWidget(self.add_region_button)
        
        layout.addLayout(new_region_layout)

        # Summary table
        columns = ['Region Name', 'Selected Tiles', 'Enhancement Data']
        self.region_table = QTableWidget()
        self.region_table.setFixedHeight(150)
        self.region_table.setColumnCount(len(columns))
        self.region_table.setHorizontalHeaderLabels(columns)
        self.region_table.itemSelectionChanged.connect(self.handle_table_item_changed)
        self.region_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.region_table)
        
        self.region_tab_widget = QTabWidget()
        layout.addWidget(self.region_tab_widget)
        
        ##########################################################################

        project_settings_tab = QWidget()
        project_settings_layout_tab = QVBoxLayout(project_settings_tab)
        horizontal_layout = QHBoxLayout()
        project_settings_layout_tab.addLayout(horizontal_layout)
        horizontal_layout.addWidget(project_settings_group)
        horizontal_layout.addWidget(image_settings_group)
        project_settings_layout_tab.addWidget(regions_group)
        project_settings_layout_tab.addStretch()
        return project_settings_tab
        
    def create_menu_bar(self):
        # Create the menu bar
        menu_bar = self.menuBar()

        # Create a File menu
        file_menu = menu_bar.addMenu("File")

        # Add 'Open Project' action
        open_action = file_menu.addAction("Open Project")
        open_action.triggered.connect(self.open_project)

        # Add 'Create New Project' action
        new_action = file_menu.addAction("Create New Project")
        new_action.triggered.connect(self.create_new_project)
        
        # Add 'Save Project' action
        save_action = file_menu.addAction("Save")
        save_action.setShortcut(QKeySequence("Ctrl+S"))  # Add Ctrl+S shortcut
        save_action.triggered.connect(self.save_project)

    def open_project(self):
        # Select directory
        project_dir = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_dir:
            config_file = os.path.join(project_dir, "config.json")
            if os.path.exists(config_file):
                # Open and parse the config.json
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                self.load_config_data(config_data)
                self.current_project_path = project_dir  # Store the project path
                self.load_project_settings_from_env()
                QMessageBox.information(self, "Success", "Project loaded successfully.")
                
                self.current_project_name = os.path.basename(project_dir)  # Extract project name from path
                self.project_name_label.setText(f"Project: {self.current_project_name}")  # Update label
            else:
                QMessageBox.warning(self, "Error", "config.json not found in the selected directory.")

    def create_new_project(self):
        # Select directory
        project_dir = QFileDialog.getExistingDirectory(self, "Select Directory for New Project")
        if project_dir:
            # Create config.json based on self.seasons
            config_file = os.path.join(project_dir, "config.json")
            
            with open(config_file, 'w') as f:
                json.dump(self.regions, f, indent=4)
            
            QMessageBox.information(self, "Success", f"New project created at {project_dir}")

            # Store the new project path and name
            self.current_project_path = project_dir
            self.current_project_name = os.path.basename(project_dir)
            self.project_name_label.setText(f"Project: {self.current_project_name}")  # Update label

    def save_project(self):
        if not self.current_project_path:
            QMessageBox.warning(self, "Error", "No project is opened or created.")
            return

        config_file = os.path.join(self.current_project_path, "config.json")
        # Save the project data to config.json
        with open(config_file, 'w') as f:
            json.dump(self.regions, f, indent=4)

        self.save_project_settings_to_env()
        
        QMessageBox.information(self, "Success", f"Project saved successfully")
        self.load_config_data(self.regions)
        
    def load_config_data(self, config_data):
        """
        This function populates the UI based on the data from config.json
        :param config_data: A dictionary parsed from config.json
        """
        if config_data:
            self.region_table.setRowCount(0)
            if config_data:
                # Load regions and enhancement data into the interface
                print(f"Loading data from config.json file...")
                for region_name, data in config_data.items():
                    # You can update your UI with the loaded data here
                    self.regions[region_name] = data
                    row_position = self.region_table.rowCount()
                    self.region_table.insertRow(row_position)
                    self.region_table.setItem(row_position, 0, QTableWidgetItem(region_name))
                    tiles = self.regions[region_name]['tiles']
                    self.region_table.setItem(self.get_region_row_number(region_name), 1, QTableWidgetItem(str(tiles)))
                    enhancement_data = self.regions[region_name]['enhancement_data']
                    self.region_table.setItem(self.get_region_row_number(region_name), 2, QTableWidgetItem(json.dumps(enhancement_data)))
                    self.region_input.clear()
                self.region_table.horizontalHeader().setStretchLastSection(True)
                self.region_table.selectRow(0)
            
    def load_project_settings_from_env(self):
        """
        Load project-specific settings from the .env file and populate relevant UI fields
        """
        load_dotenv(dotenv_path=os.path.join(self.current_project_path, '.env'), override=True)
        # Example of loading environment variables and setting UI components
        openeo_auth_client_id = os.getenv("OPENEO_AUTH_CLIENT_ID")
        openeo_auth_client_secret = os.getenv("OPENEO_AUTH_CLIENT_SECRET")
        openeo_provider = os.getenv("OPENEO_AUTH_PROVIDER_ID")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_access_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        token_username = os.getenv("TOKEN_USERNAME")
        token_password = os.getenv("TOKEN_PASSWORD")
        
        if openeo_auth_client_id:
            self.client_id_input.setText(openeo_auth_client_id)
        if openeo_auth_client_secret:
            self.client_secret_input.setText(openeo_auth_client_secret)
        if openeo_provider:
            self.provider_id_input.setText(openeo_provider)
        if aws_access_key:
            self.aws_access_key_input.setText(aws_access_key)
        if aws_access_secret:
            self.aws_secret_access_key_input.setText(aws_access_secret)
        if token_username:
            self.token_username_input.setText(token_username)
        if token_password:
            self.token_password_input.setText(token_password)
            
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT")
        email_from = os.getenv("FROM")
        email_to = os.getenv("TO")
        email_subject = os.getenv("SUBJECT")
        
        if smtp_host:
            self.smtp_host_input.setText(smtp_host)
        if smtp_port:
            self.smtp_port_input.setText(smtp_port)
        if email_from:
            self.from_input.setText(email_from)
        if email_to:
            self.to_input.setText(email_to)
        if email_subject:
            self.subject_input.setText(email_subject)
        
        
        crs = os.getenv("CRS")
        service_dir = os.getenv("SERVICE_DIR")
        threads = os.getenv("THREADS")
        max_cloud_cover = os.getenv("MAX_CLOUD_COVER")
        days_offset = os.getenv("DAYS_OFFSET")
        only_complete = True if os.getenv("ONLY_COMPLETE") == 'True' else False
        only_latest = True if os.getenv("ONLY_LATEST") == 'True' else False
        

        if crs:
            self.crs_input.setText(crs)
        if service_dir:
            self.service_dir_input.setText(service_dir)
        if threads:
            self.threads_input.setText(threads)
        if max_cloud_cover:
            self.max_cloud_cover_input.setText(max_cloud_cover)
        if days_offset:
            self.days_offset_input.setText(days_offset)
        if only_complete:
            self.only_complete.setChecked(only_complete)
        if only_latest:
            self.only_latest.setChecked(only_latest)
            
    def save_project_settings_to_env(self):
        """
        Save project-specific settings to the .env file based on the current UI field values.
        """
        # Collect settings from UI components
        openeo_auth_client_id = self.client_id_input.text()
        openeo_auth_client_secret = self.client_secret_input.text()
        openeo_provider = self.provider_id_input.text()
        aws_access_key = self.aws_access_key_input.text()
        aws_access_secret = self.aws_secret_access_key_input.text()
        token_username = self.token_username_input.text()
        token_password = self.token_password_input.text()

        smtp_host = self.smtp_host_input.text()
        smtp_port = self.smtp_port_input.text()
        email_from = self.from_input.text()
        email_to = self.to_input.toPlainText()
        email_subject = self.subject_input.text()
        
        crs = self.crs_input.text()
        service_dir = self.service_dir_input.text()
        threads = self.threads_input.text()
        max_cloud_cover = self.max_cloud_cover_input.text()
        days_offset = self.days_offset_input.text()

        # Define the content to be written to the .env file
        env_content = f"""\
# CREDENTIALS
# https://dataspace.copernicus.eu/
# https://documentation.dataspace.copernicus.eu/Registration.html
OPENEO_AUTH_CLIENT_ID={openeo_auth_client_id}
OPENEO_AUTH_CLIENT_SECRET={openeo_auth_client_secret}
OPENEO_AUTH_PROVIDER_ID={openeo_provider}

# S3_CREDENTIALS
# https://documentation.dataspace.copernicus.eu/APIs/S3.html
# https://eodata-s3keysmanager.dataspace.copernicus.eu/panel/s3-credentials
AWS_ACCESS_KEY_ID={aws_access_key}
AWS_SECRET_ACCESS_KEY={aws_access_secret}
TOKEN_USERNAME={token_username}
TOKEN_PASSWORD={token_password}

# EMAIL
SMTP_HOST={smtp_host}
SMTP_PORT={smtp_port}
FROM={email_from}
TO={email_to}
SUBJECT={email_subject}

# PROJECT_SETTINGS
SERVICE_DIR={service_dir}
THREADS={threads}

# IMAGE_SETTINGS
CRS={crs}
MAX_CLOUD_COVER={max_cloud_cover}
DAYS_OFFSET={days_offset}
ONLY_COMPLETE={self.only_complete.isChecked()}
ONLY_LATEST={self.only_latest.isChecked()}
        """

        # Write to the .env file
        try:
            env_file = os.path.join(self.current_project_path, ".env")
            with open(env_file, 'w', encoding='UTF-8') as f:
                    f.write(env_content)
                    load_dotenv(dotenv_path=env_file, override=True)
            print("Settings saved to .env file successfully.")
        except Exception as e:
            QMessageBox.critical(self, f"Failed to save settings to .env file: {e}")
        
    def add_region(self):
        region_name = self.region_input.text()
        if region_name and region_name not in self.regions:
            self.regions[region_name] = {'tiles': [], 'enhancement_data': {}}
            row_position = self.region_table.rowCount()
            self.region_table.insertRow(row_position)
            self.region_table.setItem(row_position, 0, QTableWidgetItem(region_name))
            self.region_table.selectRow(row_position)
            self.region_input.clear()
        
    def get_region_row_number(self, region_name):
        for row in range(self.region_table.rowCount()):
            if self.region_table.item(row, 0).text() == region_name:
                return row
        return -1  # Return -1 if the region is not found
    
    def handle_table_item_changed(self):
        self.update_tab()

    def update_tab(self):
        row = self.region_table.currentRow()
        if row >= 0:
            selected_region = self.region_table.item(row, 0).text()
            # Clear existing tabs and populate them with selected tiles and enhancement data
            self.region_tab_widget.clear()
            if selected_region:
                # Tab for Selected Tiles
                tiles_tab = QWidget()
                tiles_layout = QVBoxLayout()
                self.open_map_window()
                tiles_layout.addWidget(self.map_window)
                tiles_tab.setLayout(tiles_layout)

                # Tab for Enhancement Data
                enhancement_tab = QWidget()
                enhancement_layout = QVBoxLayout()
                self.open_enhancement_window(selected_region)
                enhancement_layout.addWidget(self.enhancement_window)
                enhancement_tab.setLayout(enhancement_layout)
                

                # Add tabs to the QTabWidget
                self.region_tab_widget.addTab(tiles_tab, "Selected Tiles")
                self.region_tab_widget.addTab(enhancement_tab, "Enhancement Data")

    def open_map_window(self):
        selected_row = self.region_table.currentRow()
        if selected_row >= 0:
            region_name = self.region_table.item(selected_row, 0).text()
            selected_tiles = self.regions.get(region_name, {}).get('tiles', [])
            self.map_window = MapWindow(selected_tiles, region_name)
            self.map_window.selected_tiles_signal.connect(self.handle_selected_tiles)
            #self.map_window.map_closed_signal.connect(self.open_enhancement_window)
            #self.map_window.show()

    @pyqtSlot(list)
    def handle_selected_tiles(self, selected_tiles):
        selected_row = self.region_table.currentRow()
        if selected_row >= 0:
            region_name = self.region_table.item(selected_row, 0).text()
            self.regions[region_name]['tiles'] = selected_tiles
            self.save_project()
            
    def open_enhancement_window(self, region_name):
        self.enhancement_window = RegionInputWindow(region_name, self.regions[region_name]['enhancement_data'])
        self.enhancement_window.region_added_signal.connect(self.handle_enhancement_data)
        #self.enhancement_window.show()
        
    @pyqtSlot(str, dict)
    def handle_enhancement_data(self, region_name, enhancement_data):
        self.regions[region_name]['enhancement_data'] = enhancement_data
        self.save_project()
        
    def execute_process(self):
        self.worker = Worker(self.send_notification_checkbox.isChecked(), self.current_project_path, self.status_label)
        self.worker.update_progress.connect(self.update_status)
        self.status_label.setText("Process started...")
        self.worker.start()  # Start the worker thread
    
    def update_status(self, message):
        self.status_label.setText(message)
        
    def closeEvent(self, event):
        # Stop the thread and ensure it exits
        if self.worker:
            self.worker.stop()
            self.worker.join()
        super().closeEvent(event)
        
        
class Worker(QThread):
    # Signal to communicate with the main thread
    update_progress = pyqtSignal(str)
    
    def __init__(self, send_email, current_project_path, status_label):
        super().__init__()
        self.send_email = send_email
        self.current_project_path = current_project_path
        self.status_label = status_label

    def run(self):
        try:
            if main_process(self.current_project_path, self.send_email):
                self.status_label.setText('Process successfully completed!')
        except Exception as e:
            print(e)
            self.status_label.setText(f'Something went wrong! Check log file for more information.')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont('Arial', 8)  # Set font family and size
    app.setFont(font)
    window = ProjectWindow()
    window.show()
    app.exec_()
