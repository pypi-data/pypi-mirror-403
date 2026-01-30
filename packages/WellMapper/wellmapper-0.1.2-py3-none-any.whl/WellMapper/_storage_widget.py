"""Parameter widget for configuring storage settings with status display and export format selection"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QGroupBox,
    QMessageBox, QFileDialog, QTextEdit, QFrame, QCheckBox, QHBoxLayout
)
from qtpy.QtCore import Qt
from pathlib import Path
import os


class StorageStatusWidget(QFrame):
    """Widget to display current storage configuration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("<b>Current Storage Configuration</b>")
        layout.addWidget(title)
        
        self.status_label = QLabel("No storage configured")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.example_label = QLabel()
        self.example_label.setWordWrap(True)
        self.example_label.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        layout.addWidget(self.example_label)
        
        self.setLayout(layout)
    
    def update_status(self, config):
        """Update the status display based on current config"""
        storage_type = config.get("STORAGE_TYPE", "local")
        formats = config.get("EXPORT_FORMATS", "csv").split(",")
        formats_str = ", ".join(formats)
        
        if storage_type == "local":
            path = config.get("STORAGE_PATH", "./data")
            self.status_label.setText(
                f"✓ <b>Local Storage</b><br>"
                f"Path: {path}<br>"
                f"Formats: {formats_str}"
            )
            example_files = [f"{path}/plate_ABC123.{fmt}" for fmt in formats]
            self.example_label.setText(
                "Examples:<br>" + "<br>".join(example_files)
            )
        
        elif storage_type == "s3":
            bucket = config.get("S3_BUCKET", "")
            prefix = config.get("S3_PREFIX", "")
            region = config.get("AWS_REGION", "")
            has_creds = bool(config.get("AWS_ACCESS_KEY_ID"))
            
            if bucket:
                creds_text = "✓ Credentials configured" if has_creds else "Using IAM role/AWS CLI"
                self.status_label.setText(
                    f"✓ <b>AWS S3 Storage</b><br>"
                    f"Bucket: {bucket}<br>"
                    f"Prefix: {prefix or '(root)'}<br>"
                    f"Region: {region or '(default)'}<br>"
                    f"{creds_text}<br>"
                    f"Formats: {formats_str}"
                )
                example_files = []
                for fmt in formats:
                    example_key = f"{prefix}/plate_ABC123.{fmt}" if prefix else f"plate_ABC123.{fmt}"
                    example_files.append(f"s3://{bucket}/{example_key}")
                self.example_label.setText(
                    "Examples:<br>" + "<br>".join(example_files)
                )
            else:
                self.status_label.setText("S3 storage selected but not configured")
                self.example_label.setText("")
        
        elif storage_type == "azure":
            container = config.get("AZURE_CONTAINER", "")
            prefix = config.get("AZURE_PREFIX", "")
            has_conn = bool(config.get("AZURE_STORAGE_CONNECTION_STRING"))
            
            if container and has_conn:
                self.status_label.setText(
                    f"✓ <b>Azure Blob Storage</b><br>"
                    f"Container: {container}<br>"
                    f"Prefix: {prefix or '(root)'}<br>"
                    f"✓ Connection string configured<br>"
                    f"Formats: {formats_str}"
                )
                example_files = []
                for fmt in formats:
                    example_blob = f"{prefix}/plate_ABC123.{fmt}" if prefix else f"plate_ABC123.{fmt}"
                    example_files.append(f"azure://{container}/{example_blob}")
                self.example_label.setText(
                    "Examples:<br>" + "<br>".join(example_files)
                )
            else:
                self.status_label.setText("Azure storage selected but not configured")
                self.example_label.setText("")
        
        elif storage_type == "gcs":
            bucket = config.get("GCS_BUCKET", "")
            prefix = config.get("GCS_PREFIX", "")
            creds = config.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            
            if bucket:
                creds_text = f"✓ Credentials: {Path(creds).name}" if creds else "Using default credentials"
                self.status_label.setText(
                    f"✓ <b>Google Cloud Storage</b><br>"
                    f"Bucket: {bucket}<br>"
                    f"Prefix: {prefix or '(root)'}<br>"
                    f"{creds_text}<br>"
                    f"Formats: {formats_str}"
                )
                example_files = []
                for fmt in formats:
                    example_key = f"{prefix}/plate_ABC123.{fmt}" if prefix else f"plate_ABC123.{fmt}"
                    example_files.append(f"gs://{bucket}/{example_key}")
                self.example_label.setText(
                    "Examples:<br>" + "<br>".join(example_files)
                )
            else:
                self.status_label.setText("GCS storage selected but not configured")
                self.example_label.setText("")
        else:
            self.status_label.setText("No storage configured")
            self.example_label.setText("")


class StorageConfigWidget(QWidget):
    """Widget for configuring storage backend settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Storage Configuration")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Status display at top
        self.status_widget = StorageStatusWidget()
        layout.addWidget(self.status_widget)
        
        # Storage type selector
        type_group = QGroupBox("Storage Backend")
        type_layout = QFormLayout()
        
        self.storage_type = QComboBox()
        self.storage_type.addItems(["local", "s3", "azure", "gcs"])
        self.storage_type.currentTextChanged.connect(self.on_storage_type_changed)
        type_layout.addRow("Storage Type:", self.storage_type)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Export format selection
        format_group = QGroupBox("Export Formats")
        format_layout = QHBoxLayout()
        
        self.csv_checkbox = QCheckBox("CSV")
        self.csv_checkbox.setChecked(True)  # Default
        format_layout.addWidget(self.csv_checkbox)
        
        self.parquet_checkbox = QCheckBox("Parquet")
        format_layout.addWidget(self.parquet_checkbox)
        
        self.xlsx_checkbox = QCheckBox("Excel (XLSX)")
        format_layout.addWidget(self.xlsx_checkbox)
        
        format_note = QLabel("Note: Parquet and XLSX require pandas to be installed")
        format_note.setWordWrap(True)
        format_note.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        
        format_group_layout = QVBoxLayout()
        format_group_layout.addLayout(format_layout)
        format_group_layout.addWidget(format_note)
        format_group.setLayout(format_group_layout)
        layout.addWidget(format_group)
        
        # Local storage settings
        self.local_group = QGroupBox("Local Storage Settings")
        local_layout = QFormLayout()
        
        self.local_path = QLineEdit()
        local_path_btn = QPushButton("Browse...")
        local_path_btn.clicked.connect(self.browse_local_path)
        
        path_layout = QVBoxLayout()
        path_layout.addWidget(self.local_path)
        path_layout.addWidget(local_path_btn)
        
        local_layout.addRow("Storage Path:", path_layout)
        self.local_group.setLayout(local_layout)
        layout.addWidget(self.local_group)
        
        # S3 settings
        self.s3_group = QGroupBox("AWS S3 Settings")
        s3_layout = QFormLayout()
        
        self.s3_bucket = QLineEdit()
        self.s3_prefix = QLineEdit()
        self.s3_region = QLineEdit()
        self.s3_region.setPlaceholderText("e.g., us-east-1")
        self.s3_access_key = QLineEdit()
        self.s3_secret_key = QLineEdit()
        self.s3_secret_key.setEchoMode(QLineEdit.Password)
        
        s3_layout.addRow("Bucket Name:", self.s3_bucket)
        s3_layout.addRow("Prefix (optional):", self.s3_prefix)
        s3_layout.addRow("Region:", self.s3_region)
        s3_layout.addRow("Access Key ID:", self.s3_access_key)
        s3_layout.addRow("Secret Access Key:", self.s3_secret_key)
        
        s3_note = QLabel("Note: Leave credentials empty to use AWS CLI config or IAM role")
        s3_note.setWordWrap(True)
        s3_note.setStyleSheet("color: gray; font-style: italic;")
        s3_layout.addRow(s3_note)
        
        self.s3_group.setLayout(s3_layout)
        layout.addWidget(self.s3_group)
        
        # Azure settings
        self.azure_group = QGroupBox("Azure Blob Storage Settings")
        azure_layout = QFormLayout()
        
        self.azure_connection_string = QTextEdit()
        self.azure_connection_string.setMaximumHeight(60)
        self.azure_connection_string.setPlaceholderText(
            "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
        )
        self.azure_container = QLineEdit()
        self.azure_prefix = QLineEdit()
        
        azure_layout.addRow("Connection String:", self.azure_connection_string)
        azure_layout.addRow("Container Name:", self.azure_container)
        azure_layout.addRow("Prefix (optional):", self.azure_prefix)
        
        self.azure_group.setLayout(azure_layout)
        layout.addWidget(self.azure_group)
        
        # GCS settings
        self.gcs_group = QGroupBox("Google Cloud Storage Settings")
        gcs_layout = QFormLayout()
        
        self.gcs_bucket = QLineEdit()
        self.gcs_prefix = QLineEdit()
        self.gcs_project = QLineEdit()
        self.gcs_credentials = QLineEdit()
        gcs_cred_btn = QPushButton("Browse...")
        gcs_cred_btn.clicked.connect(self.browse_gcs_credentials)
        
        cred_layout = QVBoxLayout()
        cred_layout.addWidget(self.gcs_credentials)
        cred_layout.addWidget(gcs_cred_btn)
        
        gcs_layout.addRow("Bucket Name:", self.gcs_bucket)
        gcs_layout.addRow("Prefix (optional):", self.gcs_prefix)
        gcs_layout.addRow("Project ID:", self.gcs_project)
        gcs_layout.addRow("Credentials JSON:", cred_layout)
        
        self.gcs_group.setLayout(gcs_layout)
        layout.addWidget(self.gcs_group)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_config)
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initially hide all config groups
        self.on_storage_type_changed(self.storage_type.currentText())
    
    def on_storage_type_changed(self, storage_type):
        """Show/hide relevant configuration sections"""
        self.local_group.setVisible(storage_type == "local")
        self.s3_group.setVisible(storage_type == "s3")
        self.azure_group.setVisible(storage_type == "azure")
        self.gcs_group.setVisible(storage_type == "gcs")
    
    def browse_local_path(self):
        """Browse for local storage directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Storage Directory",
            self.local_path.text() or str(Path.home())
        )
        if path:
            self.local_path.setText(path)
    
    def browse_gcs_credentials(self):
        """Browse for GCS credentials JSON file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GCS Credentials JSON",
            self.gcs_credentials.text() or str(Path.home()),
            "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self.gcs_credentials.setText(path)
    
    def get_export_formats(self):
        """Get list of selected export formats"""
        formats = []
        if self.csv_checkbox.isChecked():
            formats.append("csv")
        if self.parquet_checkbox.isChecked():
            formats.append("parquet")
        if self.xlsx_checkbox.isChecked():
            formats.append("xlsx")
        
        if not formats:
            # At least one format must be selected
            self.csv_checkbox.setChecked(True)
            formats.append("csv")
        
        return formats
    
    def get_current_config(self):
        """Get current configuration as dict"""
        config = {}
        config["STORAGE_TYPE"] = self.storage_type.currentText()
        config["EXPORT_FORMATS"] = ",".join(self.get_export_formats())
        
        if config["STORAGE_TYPE"] == "local":
            config["STORAGE_PATH"] = self.local_path.text()
        elif config["STORAGE_TYPE"] == "s3":
            config["S3_BUCKET"] = self.s3_bucket.text()
            config["S3_PREFIX"] = self.s3_prefix.text()
            config["AWS_REGION"] = self.s3_region.text()
            config["AWS_ACCESS_KEY_ID"] = self.s3_access_key.text()
            config["AWS_SECRET_ACCESS_KEY"] = self.s3_secret_key.text()
        elif config["STORAGE_TYPE"] == "azure":
            config["AZURE_STORAGE_CONNECTION_STRING"] = self.azure_connection_string.toPlainText()
            config["AZURE_CONTAINER"] = self.azure_container.text()
            config["AZURE_PREFIX"] = self.azure_prefix.text()
        elif config["STORAGE_TYPE"] == "gcs":
            config["GCS_BUCKET"] = self.gcs_bucket.text()
            config["GCS_PREFIX"] = self.gcs_prefix.text()
            config["GCS_PROJECT"] = self.gcs_project.text()
            config["GOOGLE_APPLICATION_CREDENTIALS"] = self.gcs_credentials.text()
        
        return config
    
    def load_current_config(self):
        """Load current configuration from .env file"""
        env_path = Path(".env")
        if not env_path.exists():
            self.status_widget.update_status({})
            return
        
        # Read .env file
        config = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key] = value
        
        # Load values into form
        storage_type = config.get("STORAGE_TYPE", "local")
        idx = self.storage_type.findText(storage_type)
        if idx >= 0:
            self.storage_type.setCurrentIndex(idx)
        
        # Load export formats
        formats = config.get("EXPORT_FORMATS", "csv").split(",")
        self.csv_checkbox.setChecked("csv" in formats)
        self.parquet_checkbox.setChecked("parquet" in formats)
        self.xlsx_checkbox.setChecked("xlsx" in formats)
        
        # Local
        self.local_path.setText(config.get("STORAGE_PATH", "./data"))
        
        # S3
        self.s3_bucket.setText(config.get("S3_BUCKET", ""))
        self.s3_prefix.setText(config.get("S3_PREFIX", ""))
        self.s3_region.setText(config.get("AWS_REGION", ""))
        self.s3_access_key.setText(config.get("AWS_ACCESS_KEY_ID", ""))
        self.s3_secret_key.setText(config.get("AWS_SECRET_ACCESS_KEY", ""))
        
        # Azure
        self.azure_connection_string.setPlainText(config.get("AZURE_STORAGE_CONNECTION_STRING", ""))
        self.azure_container.setText(config.get("AZURE_CONTAINER", "data"))
        self.azure_prefix.setText(config.get("AZURE_PREFIX", ""))
        
        # GCS
        self.gcs_bucket.setText(config.get("GCS_BUCKET", ""))
        self.gcs_prefix.setText(config.get("GCS_PREFIX", ""))
        self.gcs_project.setText(config.get("GCS_PROJECT", ""))
        self.gcs_credentials.setText(config.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
        
        # Update status display
        self.status_widget.update_status(config)
    
    def save_config(self):
        """Save configuration to .env file"""
        storage_type = self.storage_type.currentText()
        formats = self.get_export_formats()
        
        lines = [
            "# WellMapper - Storage Configuration",
            f"STORAGE_TYPE={storage_type}",
            f"EXPORT_FORMATS={','.join(formats)}",
            ""
        ]
        
        if storage_type == "local":
            lines.extend([
                "# Local Storage",
                f"STORAGE_PATH={self.local_path.text()}",
            ])
        
        elif storage_type == "s3":
            lines.extend([
                "# AWS S3 Storage",
                f"S3_BUCKET={self.s3_bucket.text()}",
                f"S3_PREFIX={self.s3_prefix.text()}",
                f"AWS_REGION={self.s3_region.text()}",
            ])
            if self.s3_access_key.text():
                lines.extend([
                    f"AWS_ACCESS_KEY_ID={self.s3_access_key.text()}",
                    f"AWS_SECRET_ACCESS_KEY={self.s3_secret_key.text()}",
                ])
        
        elif storage_type == "azure":
            lines.extend([
                "# Azure Blob Storage",
                f"AZURE_STORAGE_CONNECTION_STRING={self.azure_connection_string.toPlainText()}",
                f"AZURE_CONTAINER={self.azure_container.text()}",
                f"AZURE_PREFIX={self.azure_prefix.text()}",
            ])
        
        elif storage_type == "gcs":
            lines.extend([
                "# Google Cloud Storage",
                f"GCS_BUCKET={self.gcs_bucket.text()}",
                f"GCS_PREFIX={self.gcs_prefix.text()}",
                f"GCS_PROJECT={self.gcs_project.text()}",
                f"GOOGLE_APPLICATION_CREDENTIALS={self.gcs_credentials.text()}",
            ])
        
        # Write .env file
        env_path = Path(".env")
        with open(env_path, "w") as f:
            f.write("\n".join(lines))
        
        # Update status display
        self.status_widget.update_status(self.get_current_config())
        
        formats_str = ", ".join(formats)
        QMessageBox.information(
            self,
            "Configuration Saved",
            f"Storage configuration saved to {env_path.absolute()}\n\n"
            f"Export formats: {formats_str}\n\n"
            "Configuration will be used automatically."
        )
    
    def test_connection(self):
        """Test the storage connection"""
        storage_type = self.storage_type.currentText()
        
        try:
            # Temporarily set environment variables
            if storage_type == "local":
                os.environ["STORAGE_TYPE"] = "local"
                os.environ["STORAGE_PATH"] = self.local_path.text()
            
            elif storage_type == "s3":
                os.environ["STORAGE_TYPE"] = "s3"
                os.environ["S3_BUCKET"] = self.s3_bucket.text()
                os.environ["S3_PREFIX"] = self.s3_prefix.text()
                os.environ["AWS_REGION"] = self.s3_region.text()
                if self.s3_access_key.text():
                    os.environ["AWS_ACCESS_KEY_ID"] = self.s3_access_key.text()
                    os.environ["AWS_SECRET_ACCESS_KEY"] = self.s3_secret_key.text()
            
            elif storage_type == "azure":
                os.environ["STORAGE_TYPE"] = "azure"
                os.environ["AZURE_STORAGE_CONNECTION_STRING"] = self.azure_connection_string.toPlainText()
                os.environ["AZURE_CONTAINER"] = self.azure_container.text()
                os.environ["AZURE_PREFIX"] = self.azure_prefix.text()
            
            elif storage_type == "gcs":
                os.environ["STORAGE_TYPE"] = "gcs"
                os.environ["GCS_BUCKET"] = self.gcs_bucket.text()
                os.environ["GCS_PREFIX"] = self.gcs_prefix.text()
                os.environ["GCS_PROJECT"] = self.gcs_project.text()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.gcs_credentials.text()
            
            # Try to create storage backend
            try:
                from WellMapper.storage_backends import create_storage_backend
            except ImportError:
                from storage_backends import create_storage_backend
                
            storage = create_storage_backend()
            
            # Try to write a test file
            test_content = "test,connection,123"
            result = storage.write("test_connection.csv", test_content)
            
            QMessageBox.information(
                self,
                "Connection Successful",
                f"Successfully connected to {storage_type} storage!\n\n"
                f"Test file written to:\n{result}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to {storage_type} storage:\n\n{str(e)}"
            )


def set_storage_solution():
    """Entry point for napari plugin"""
    return StorageConfigWidget()