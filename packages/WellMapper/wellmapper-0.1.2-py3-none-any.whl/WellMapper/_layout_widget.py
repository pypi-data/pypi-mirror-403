from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDateEdit, QSpinBox, QCompleter,
    QGroupBox, QMessageBox, QFrame
)
from qtpy.QtCore import Qt, QDate
from qtpy.QtGui import QColor, QPalette
from pathlib import Path
from natsort import natsorted
import yaml
import os

# Import storage backend (dotenv loading happens inside create_storage_backend)
try:
    from .storage_backends import create_storage_backend
except ImportError:
    from storage_backends import create_storage_backend


def load_plate_config(path="plate_config.yaml"):
    base_dir = Path(__file__).resolve().parent
    cfg_path = base_dir / path
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r") as f:
        return yaml.safe_load(f)


class WellData:
    def __init__(self):
        self.values = {}

    def is_empty(self):
        return all(not v for v in self.values.values())

    def is_incomplete(self):
        filled = sum(bool(v) for v in self.values.values())
        return 0 < filled < len(self.values)

    def color_hash(self):
        """Generate consistent, well-separated color from well values"""
        s = "".join(self.values.get(k, "") for k in sorted(self.values.keys()))
        if not s:
            return QColor(255, 255, 255)
        h = 0
        for i, c in enumerate(s):
            h = (h * 37 + ord(c) + i * 13) & 0xFFFFFFFF  # larger multiplier for better spread
        hue = h % 360
        saturation = 200 + (h % 55)   # 200-255 vibrant
        lightness = 120 + ((h // 360) % 80)  # 120-199 good contrast
        return QColor.fromHsl(hue, saturation, lightness)

class ColorInfoWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        self.color_label = QLabel()
        self.color_label.setFixedSize(40, 40)
        self.color_label.setFrameStyle(QFrame.Box)
        self.color_label.setLineWidth(2)
        layout.addWidget(self.color_label)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label, 1)
        self.setLayout(layout)
        self.hide()

    def show_info(self, well_name, well_data, color):
        palette = self.color_label.palette()
        palette.setColor(QPalette.Window, color)
        self.color_label.setAutoFillBackground(True)
        self.color_label.setPalette(palette)

        if well_data.is_empty():
            self.info_label.setText(f"<b>{well_name}</b>: Empty well")
        elif well_data.is_incomplete():
            info_parts = [f"{k}: {v}" for k, v in well_data.values.items() if v]
            self.info_label.setText(
                f"<b>{well_name}</b> - <span style='color: orange;'>⚠ Incomplete</span><br>"
                + ", ".join(info_parts)
            )
        else:
            info_parts = [f"{k}: {v}" for k, v in well_data.values.items()]
            self.info_label.setText(f"<b>{well_name}</b><br>" + " | ".join(info_parts))
        self.show()

    def clear_info(self):
        self.hide()


class PlateLayoutWidget(QWidget):
    def __init__(self, napari_viewer=None):
        super().__init__()
        self.viewer = napari_viewer
        self.config = load_plate_config()
        self.exp_cfg = self.config["experiment_information"]
        self.well_cfg = self.config["well_information"]

        self.ROWS = self.exp_cfg["rows"].get("default", 8)
        self.COLS = self.exp_cfg["cols"].get("default", 12)
        self.setMinimumWidth(750)

        self.well_data = {}
        self.selected_wells = set()
        for r in range(self.ROWS):
            for c in range(1, self.COLS + 1):
                self.well_data[f"{chr(65+r)}{c}"] = WellData()

        self.exp_fields = {}  # input widgets
        self.well_fields = {}  # input widgets
        
        # Initialize storage backend (will load from .env automatically)
        try:
            self.storage = create_storage_backend()
            storage_type = os.getenv("STORAGE_TYPE", "local")
            print(f"Initialized {storage_type} storage backend")
        except ImportError as e:
            # Missing dependencies for cloud storage
            storage_type = os.getenv("STORAGE_TYPE", "local")
            QMessageBox.warning(
                self, 
                "Storage Setup Required", 
                f"Cloud storage dependencies missing:\n\n{str(e)}\n\n"
                f"Falling back to local storage."
            )
            try:
                from .storage_backends import LocalStorage
            except ImportError:
                from storage_backends import LocalStorage
            self.storage = LocalStorage()
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Storage Warning", 
                f"Could not initialize storage backend: {e}\n\n"
                f"Falling back to local storage."
            )
            try:
                from .storage_backends import LocalStorage
            except ImportError:
                from storage_backends import LocalStorage
            self.storage = LocalStorage()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # ---- Experiment Info ----
        self.global_group = QGroupBox("Experiment Information")
        g_layout = QFormLayout()
        for key, cfg in self.exp_cfg.items():
            if cfg["type"] == "int":
                spin = QSpinBox()
                spin.setRange(cfg.get("min", 0), cfg.get("max", 1000))
                spin.setValue(cfg.get("default", 0))
                g_layout.addRow(cfg["label"], spin)
                self.exp_fields[key] = spin
            elif cfg["type"] == "date":
                date_edit = QDateEdit()
                if cfg.get("default") == "today":
                    date_edit.setDate(QDate.currentDate())
                date_edit.setCalendarPopup(True)
                g_layout.addRow(cfg["label"], date_edit)
                self.exp_fields[key] = date_edit
            else:  # text
                txt = QLineEdit()
                txt.setText(cfg.get("default", ""))
                g_layout.addRow(cfg["label"], txt)
                self.exp_fields[key] = txt
        confirm_btn = QPushButton("Confirm Experiment Info")
        confirm_btn.clicked.connect(self.confirm_global_params)
        g_layout.addRow(confirm_btn)
        self.global_group.setLayout(g_layout)
        layout.addWidget(self.global_group)

        # ---- Well Info ----
        self.well_group = QGroupBox("Per-Well Information")
        w_layout = QFormLayout()
        for key, cfg in self.well_cfg.items():
            txt = QLineEdit()
            if "completer" in cfg:
                txt.setCompleter(QCompleter(cfg["completer"]))
            w_layout.addRow(cfg["label"], txt)
            self.well_fields[key] = txt
        self.well_group.setLayout(w_layout)
        self.well_group.setVisible(False)
        layout.addWidget(self.well_group)

        # ---- Buttons ----
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply to Selected")
        apply_btn.clicked.connect(self.apply_to_selected)
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_csv)
        clear_btn = QPushButton("Clear All Wells")
        clear_btn.clicked.connect(self.clear_all)
        for b in (apply_btn, export_btn, clear_btn):
            btn_layout.addWidget(b)
        self.button_widget = QWidget()
        self.button_widget.setLayout(btn_layout)
        self.button_widget.setVisible(False)
        layout.addWidget(self.button_widget)

        # ---- Plate Table ----
        self.table = QTableWidget(self.ROWS, self.COLS)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setHorizontalHeaderLabels([str(i+1) for i in range(self.COLS)])
        self.table.setVerticalHeaderLabels([chr(65+i) for i in range(self.ROWS)])
        for r in range(self.ROWS):
            for c in range(self.COLS):
                name = f"{chr(65+r)}{c+1}"
                item = QTableWidgetItem(name)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemClicked.connect(self.on_cell_clicked)
        self.table.horizontalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setVisible(False)
        layout.addWidget(self.table)

        # ---- Color Info Widget ----
        self.color_info = ColorInfoWidget()
        layout.addWidget(self.color_info)

        self.setLayout(layout)

    def confirm_global_params(self):
        if not self.exp_fields["barcode"].text().strip():
            QMessageBox.warning(self, "Error", "Barcode required")
            return

        self.ROWS = self.exp_fields["rows"].value()
        self.COLS = self.exp_fields["cols"].value()

        self.table.setRowCount(self.ROWS)
        self.table.setColumnCount(self.COLS)
        self.table.setVerticalHeaderLabels([chr(65+i) for i in range(self.ROWS)])
        self.table.setHorizontalHeaderLabels([str(i+1) for i in range(self.COLS)])

        self.well_data.clear()
        for r in range(self.ROWS):
            for c in range(1, self.COLS+1):
                self.well_data[f"{chr(65+r)}{c}"] = WellData()

        self.global_group.setVisible(False)
        self.well_group.setVisible(True)
        self.button_widget.setVisible(True)
        self.table.setVisible(True)

    def on_selection_changed(self):
        self.selected_wells = {f"{chr(65+i.row())}{i.column()+1}" for i in self.table.selectedItems()}

    def apply_to_selected(self):
        for well in self.selected_wells:
            wd = self.well_data[well]
            for key, widget in self.well_fields.items():
                wd.values[key] = widget.text()
            self.update_cell(well)
        self.table.clearSelection()

    def update_cell(self, well):
        r = ord(well[0]) - 65
        c = int(well[1:]) - 1
        item = self.table.item(r, c)
        wd = self.well_data[well]

        # Color
        item.setBackground(wd.color_hash())

        # Text / warning
        if wd.is_empty():
            item.setText(well)
            font = item.font()
            font.setBold(False)
            item.setFont(font)
        elif wd.is_incomplete():
            item.setText(f"{well} !")
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QColor(255, 200, 0))  # yellow warning
        else:
            item.setText(well)
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            item.setForeground(QColor(255, 255, 255))

    def on_cell_clicked(self, item):
        row, col = item.row(), item.column()
        well_name = f"{chr(65+row)}{col+1}"
        well_data = self.well_data[well_name]
        self.color_info.show_info(well_name, well_data, well_data.color_hash())


    def clear_all(self):
        for wd in self.well_data.values():
            wd.values = {}
        for r in range(self.ROWS):
            for c in range(self.COLS):
                self.table.item(r, c).setBackground(QColor(255,255,255))

    def export_csv(self):
        """Export plate layout to configured storage backend in selected formats"""
        try:
            # Get configured export formats
            formats = os.getenv("EXPORT_FORMATS", "csv").split(",")
            barcode = self.exp_fields['barcode'].text()
            
            # Define which experiment fields are structural (not data columns)
            structural_fields = {"cols", "rows"}
            
            # Get all experiment fields that should be columns (excluding structural ones)
            exp_columns = [key for key in self.exp_cfg.keys() if key not in structural_fields]
            
            # Build CSV header
            well_columns = list(self.well_cfg.keys())
            header = exp_columns + ["well"] + well_columns
            
            # Get experiment-level values
            exp_values = {}
            for key in exp_columns:
                if key not in self.exp_fields:
                    exp_values[key] = ""
                elif hasattr(self.exp_fields[key], 'date'):  # QDateEdit
                    exp_values[key] = self.exp_fields[key].date().toString("yyyy-MM-dd")
                elif hasattr(self.exp_fields[key], 'value'):  # int, double, etc.
                    exp_values[key] = str(self.exp_fields[key].value())
                elif hasattr(self.exp_fields[key], 'text'):  # text fields
                    exp_values[key] = self.exp_fields[key].text()
                else:
                    exp_values[key] = str(self.exp_fields[key])
            
            # Build data rows as list of dicts (for pandas compatibility)
            data_rows = []
            for well in natsorted(self.well_data):
                wd = self.well_data[well]
                if wd.is_empty(): 
                    continue
                
                row_dict = {}
                # Add experiment values
                for k in exp_columns:
                    row_dict[k] = exp_values.get(k, "")
                # Add well identifier
                row_dict["well"] = well
                # Add well values
                for k in well_columns:
                    row_dict[k] = str(wd.values.get(k, ""))
                
                data_rows.append(row_dict)
            
            if not data_rows:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No wells with data to export. Please fill in well information."
                )
                return
            
            # Export in each selected format
            exported_files = []
            for format in formats:
                try:
                    filename = f"{barcode}/layout"  # Extension will be added by backend
                    result_path = self.storage.write_dataframe(filename, data_rows, format.strip())
                    exported_files.append(result_path)
                except ImportError as e:
                    QMessageBox.warning(
                        self,
                        f"{format.upper()} Export Failed",
                        f"Cannot export to {format.upper()} format:\n\n{str(e)}\n\n"
                        f"Install required packages:\n"
                        f"pip install pandas  # For Parquet and XLSX\n"
                        f"pip install pyarrow  # For Parquet\n"
                        f"pip install openpyxl  # For XLSX"
                    )
                    continue
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        f"{format.upper()} Export Failed",
                        f"Failed to export {format.upper()}:\n\n{str(e)}"
                    )
                    continue
            
            if exported_files:
                files_list = "\n".join(exported_files)
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Exported {len(exported_files)} file(s):\n\n{files_list}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    "Failed to export any files. Check your configuration and try again."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export files:\n{str(e)}"
            )

def create_plate_layout_widget():
    return PlateLayoutWidget()