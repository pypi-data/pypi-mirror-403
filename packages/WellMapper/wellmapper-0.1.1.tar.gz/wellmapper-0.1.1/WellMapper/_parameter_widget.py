from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QTextEdit, QPushButton, QLabel, QMessageBox, QGroupBox, QScrollArea
)
from qtpy.QtCore import Qt
from pathlib import Path
import yaml

CONFIG_FILE = Path("./WellMapper/plate_config.yaml")
MANDATORY_EXPERIMENT_KEYS = ["rows", "cols", "barcode", "date"]

FIELD_TYPES = ["text", "int", "date"]


class ConfigEditorWidget(QWidget):
    """GUI to create/edit plate_config.yaml dynamically"""
    def __init__(self, config_file=CONFIG_FILE):
        super().__init__()
        self.setWindowTitle("Plate Config Editor")
        self.config_file = config_file
        self.config = self.load_config()
        self.field_widgets = {"experiment_information": {}, "well_information": {}}

        layout = QVBoxLayout()

        # Experiment info group
        self.exp_group = QGroupBox("Experiment Information")
        self.exp_form = QFormLayout()
        self.exp_group.setLayout(self.exp_form)
        layout.addWidget(self.exp_group)

        # Well info group
        self.well_group = QGroupBox("Well Information")
        self.well_form = QFormLayout()
        self.well_group.setLayout(self.well_form)
        layout.addWidget(self.well_group)

        # Add buttons
        btn_layout = QHBoxLayout()
        self.add_exp_btn = QPushButton("Add Experiment Field")
        self.add_exp_btn.clicked.connect(lambda: self.add_field("experiment_information"))
        self.add_well_btn = QPushButton("Add Well Field")
        self.add_well_btn.clicked.connect(lambda: self.add_field("well_information"))
        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.save_config)
        for b in [self.add_exp_btn, self.add_well_btn, self.save_btn]:
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Populate existing fields
        for section in ["experiment_information", "well_information"]:
            for key, val in self.config.get(section, {}).items():
                self.add_field(section, key, val)

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f)
        # default template
        return {
            "experiment_information": {
                "rows": {"label": "Rows", "type": "int", "required": True, "default": 8, "min": 1, "max": 26},
                "cols": {"label": "Columns", "type": "int", "required": True, "default": 12, "min": 1, "max": 50},
                "barcode": {"label": "Barcode", "type": "text", "required": True},
                "date": {"label": "Date", "type": "date", "required": True}
            },
            "well_information": {
                "donor": {"label": "Donor", "type": "text"},
                "condition": {"label": "Condition", "type": "text", "completer": ["DMSO","770"]},
                "forskolin_concentration_µM": {"label": "Concentration (µM)", "type": "text"},
                "duplicate": {"label": "Duplicate", "type": "int"}
            }
        }

    def add_field(self, section, key=None, field_data=None):
        """Add a new field row in the GUI"""
        field_data = field_data or {"label": "", "type": "text"}
        key = key or ""

        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0,0,0,0)
        row_widget.setLayout(row_layout)

        key_edit = QLineEdit(key)
        key_edit.setPlaceholderText("Key")
        row_layout.addWidget(key_edit)

        label_edit = QLineEdit(field_data.get("label", ""))
        label_edit.setPlaceholderText("Label")
        row_layout.addWidget(label_edit)

        type_combo = QComboBox()
        type_combo.addItems(FIELD_TYPES)
        type_combo.setCurrentText(field_data.get("type","text"))
        row_layout.addWidget(type_combo)

        default_edit = QLineEdit(str(field_data.get("default","")))
        default_edit.setPlaceholderText("Default")
        row_layout.addWidget(default_edit)

        completer_edit = QLineEdit(",".join(field_data.get("completer",[])))
        completer_edit.setPlaceholderText("Completer (comma-separated)")
        row_layout.addWidget(completer_edit)

        min_edit = QSpinBox()
        min_edit.setRange(-99999, 99999)
        min_edit.setValue(field_data.get("min",0))
        row_layout.addWidget(min_edit)

        max_edit = QSpinBox()
        max_edit.setRange(-99999, 99999)
        max_edit.setValue(field_data.get("max",1000))
        row_layout.addWidget(max_edit)

        remove_btn = QPushButton("Remove")
        row_layout.addWidget(remove_btn)
        # disable remove for mandatory keys
        if section=="experiment_information" and key in MANDATORY_EXPERIMENT_KEYS:
            remove_btn.setDisabled(True)
        remove_btn.clicked.connect(lambda: self.remove_field(section, key_edit, row_widget))

        # save refs
        self.field_widgets[section][key_edit] = (row_widget, key_edit, label_edit, type_combo,
                                                default_edit, completer_edit, min_edit, max_edit)

        if section=="experiment_information":
            self.exp_form.addRow(row_widget)
        else:
            self.well_form.addRow(row_widget)

    def remove_field(self, section, key_edit, row_widget):
        if section=="experiment_information" and key_edit.text() in MANDATORY_EXPERIMENT_KEYS:
            QMessageBox.warning(self, "Cannot remove", f"{key_edit.text()} is mandatory")
            return
        row_widget.setParent(None)
        del self.field_widgets[section][key_edit]

    def save_config(self):
        new_cfg = {"experiment_information": {}, "well_information": {}}
        for section in ["experiment_information", "well_information"]:
            for key_edit, widgets in self.field_widgets[section].items():
                wgt = widgets
                key_val = key_edit.text().strip()
                if not key_val: 
                    continue
                type_val = wgt[3].currentText()
                field = {"label": wgt[2].text(), "type": type_val}
                
                # Default value cast
                if wgt[4].text():
                    if type_val == "int":
                        field["default"] = int(wgt[4].text())
                    else:
                        field["default"] = wgt[4].text()
                
                # Completer
                if wgt[5].text():
                    field["completer"] = [s.strip() for s in wgt[5].text().split(",") if s.strip()]
                
                # Min/max for ints
                if type_val == "int":
                    field["min"] = wgt[6].value()
                    field["max"] = wgt[7].value()
                
                # Required for mandatory keys
                if section == "experiment_information" and key_val in MANDATORY_EXPERIMENT_KEYS:
                    field["required"] = True
                
                new_cfg[section][key_val] = field

        Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            yaml.dump(new_cfg, f, sort_keys=False)  # keep order

        QMessageBox.information(self, "Saved", f"Config saved to {self.config_file}")

def set_plate_layout_parameters():
    """Factory function for Napari command to set plate parameters"""
    return ConfigEditorWidget()