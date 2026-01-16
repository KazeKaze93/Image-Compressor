import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QFrame, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PIL import Image
from algorithms import compress_image, get_size_mb
from models import CompressionResult

# --- WORKER THREAD ---
class CompressionWorker(QThread):
    finished = pyqtSignal(CompressionResult)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, quality, output_format, resize_ratio):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.quality = quality
        self.output_format = output_format
        self.resize_ratio = resize_ratio

    def run(self):
        try:
            result = compress_image(
                self.input_path, self.output_path, self.quality, 
                self.output_format, self.resize_ratio
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# --- DRAG & DROP WIDGET ---
class DropArea(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setText("☁ Drag image here\nor click to select")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # Check file extension
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Error", "Only images are supported (JPG, PNG, WEBP)")

    def mousePressEvent(self, event):
        # Click on area opens input file selection dialog (select_input_file)
        if event.button() == Qt.LeftButton:
            self.file_dropped.emit("CLICK")

# --- MAIN WINDOW ---
class ImageCompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Compressor Pro")
        self.setFixedSize(380, 650)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(8)

        # Track original file size and dimensions for estimation
        self.original_size_mb = 0.0
        self.original_width = 0
        self.original_height = 0
        
        # Debounce timer for size estimation
        self.estimation_timer = QTimer()
        self.estimation_timer.setSingleShot(True)
        self.estimation_timer.timeout.connect(self.update_estimated_size)

        self.setup_ui()
        self.apply_stylesheet()

    def setup_ui(self):
        # 1. Drag & Drop Area
        self.drop_area = DropArea()
        self.drop_area.setFixedHeight(80)
        self.drop_area.file_dropped.connect(self.handle_file_drop)
        self.layout.addWidget(self.drop_area)

        # 2. Paths Card
        path_card = self._create_card("File Paths")
        path_layout = path_card.layout()
        path_layout.setSpacing(10)
        
        self.input_entry = self._create_row(path_layout, "Input:", read_only=True)
        self.output_entry = self._create_row(path_layout, "Output:")
        
        # Output path selection button
        self.btn_save = QPushButton("Select save location...")
        self.btn_save.setObjectName("secondaryButton")
        self.btn_save.setFixedHeight(32)
        self.btn_save.clicked.connect(self.select_output_file)
        path_layout.addWidget(self.btn_save)
        
        self.layout.addWidget(path_card)

        # 3. Settings Card
        settings_card = self._create_card("Compression Settings")
        settings_layout = settings_card.layout()
        settings_layout.setSpacing(4)
        
        # Quality Setting - QVBoxLayout structure
        quality_setting = QVBoxLayout()
        quality_setting.setSpacing(2)
        
        # Top row: QHBoxLayout with Title and Value
        quality_header = QHBoxLayout()
        quality_title = QLabel("Quality")
        quality_title.setObjectName("sectionLabel")
        self.quality_value_label = QLabel("85%")
        self.quality_value_label.setObjectName("sliderValue")
        quality_header.addWidget(quality_title)
        quality_header.addStretch()
        quality_header.addWidget(self.quality_value_label)
        quality_setting.addLayout(quality_header)
        
        # Bottom row: QSlider
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setObjectName("qualitySlider")
        self.quality_slider.valueChanged.connect(self.on_slider_changed)
        self.quality_slider.valueChanged.connect(lambda v: self.quality_value_label.setText(f"{v}%"))
        quality_setting.addWidget(self.quality_slider)
        settings_layout.addLayout(quality_setting)
        
        # Resize Setting - QVBoxLayout structure
        resize_setting = QVBoxLayout()
        resize_setting.setSpacing(2)
        
        # Top row: QHBoxLayout with Title and Value
        resize_header = QHBoxLayout()
        resize_title = QLabel("Size")
        resize_title.setObjectName("sectionLabel")
        self.resize_value_label = QLabel("100%")
        self.resize_value_label.setObjectName("sliderValue")
        resize_header.addWidget(resize_title)
        resize_header.addStretch()
        resize_header.addWidget(self.resize_value_label)
        resize_setting.addLayout(resize_header)
        
        # Bottom row: QSlider
        self.resize_slider = QSlider(Qt.Horizontal)
        self.resize_slider.setRange(1, 100)
        self.resize_slider.setValue(100)
        self.resize_slider.setObjectName("resizeSlider")
        self.resize_slider.valueChanged.connect(self.on_slider_changed)
        self.resize_slider.valueChanged.connect(lambda v: self.resize_value_label.setText(f"{v}%"))
        resize_setting.addWidget(self.resize_slider)
        settings_layout.addLayout(resize_setting)
        
        # Resolution and Estimated Size at bottom of settings card
        info_container = QVBoxLayout()
        info_container.setSpacing(2)
        
        self.resolution_label = QLabel("New Resolution: -")
        self.resolution_label.setObjectName("resolutionLabel")
        self.resolution_label.setAlignment(Qt.AlignCenter)
        info_container.addWidget(self.resolution_label)
        
        self.est_label = QLabel("Estimated Size: -")
        self.est_label.setObjectName("estimatedSizeLabel")
        self.est_label.setAlignment(Qt.AlignCenter)
        info_container.addWidget(self.est_label)
        
        settings_layout.addLayout(info_container)
        self.layout.addWidget(settings_card)

        # 4. Progress & Action
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Infinite loading style
        self.progress_bar.hide()
        self.progress_bar.setObjectName("progressBar")
        self.layout.addWidget(self.progress_bar)

        self.compress_button = QPushButton("Compress Image")
        self.compress_button.setFixedHeight(32)
        self.compress_button.setObjectName("primaryButton")
        self.compress_button.clicked.connect(self.start_compression)
        self.layout.addWidget(self.compress_button)

        self.layout.addStretch() # Push everything up

    def apply_stylesheet(self):
        """Apply minimal dark theme stylesheet"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #09090b;
            }
            
            QWidget {
                background-color: #09090b;
                color: #fafafa;
            }
            
            QFrame {
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 10px;
                background: #18181b;
            }
            
            QLabel {
                border: none;
                background: transparent;
                font-size: 10pt;
            }
            
            QLabel#estimatedSizeLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #3b82f6;
            }
            
            /* Slider Groove */
            QSlider::groove:horizontal {
                background: #27272a;
                height: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                height: 6px;
                border-radius: 3px;
            }
            
            /* Slider Handle - beautiful round shape */
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a9eff, stop:1 #3b82f6);
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
                border: 2px solid #1e3a5f;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5baaff, stop:1 #4a9eff);
                border: 2px solid #2563eb;
            }
            
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border: 2px solid #1d4ed8;
            }
            
            QLineEdit#inputField {
                background-color: #09090b;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #fafafa;
            }
            
            QLineEdit#inputField:focus {
                border-color: #3b82f6;
            }
            
            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            
            QPushButton#secondaryButton {
                background-color: #18181b;
                color: #fafafa;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 8px 16px;
            }
            
            QLabel#dropArea {
                border: 2px dashed #27272a;
                border-radius: 8px;
                padding: 8px;
                background-color: #18181b;
            }
            
            QLabel#dropArea:hover {
                border-color: #3b82f6;
            }
        """)

    def _create_card(self, title):
        """Create a card frame with QLabel header inside"""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)
        
        # Use QLabel as header instead of QGroupBox title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        card.setLayout(layout)
        return card
    
    def _create_row(self, parent_layout, label_text, read_only=False):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(60)
        lbl.setObjectName("inputLabel")
        entry = QLineEdit()
        entry.setReadOnly(read_only)
        entry.setPlaceholderText("File path...")
        entry.setObjectName("inputField")
        entry.setFixedHeight(32)
        row.addWidget(lbl)
        row.addWidget(entry)
        parent_layout.addLayout(row)
        return entry


    # --- HANDLERS ---
    def handle_file_drop(self, path):
        """
        Handles file drop or click on DropArea.
        Only updates input_entry and suggests output_entry - NEVER triggers save dialogs.
        """
        if path == "CLICK":
            # Click on DropArea triggers input file selection dialog
            self.select_input_file()
        else:
            # File was dropped or selected via dialog - update entries only
            self.input_entry.setText(path)
            # Automatically generate output path (suggestion only, no dialog)
            folder, filename = os.path.split(path)
            name, ext = os.path.splitext(filename)
            new_name = f"{name}_compressed{ext}"
            self.output_entry.setText(os.path.join(folder, new_name))
            
            # Get original file size and dimensions for estimation
            if os.path.exists(path):
                self.original_size_mb = get_size_mb(path)
                try:
                    with Image.open(path) as img:
                        self.original_width, self.original_height = img.size
                except Exception:
                    self.original_width = 0
                    self.original_height = 0
                self.update_estimated_size()
            else:
                self.original_size_mb = 0.0
                self.original_width = 0
                self.original_height = 0
                self.est_label.setText("Estimated Size: -")
                self.resolution_label.setText("New Resolution: -")

    def select_input_file(self):
        """Opens file selection dialog for input file using getOpenFileName."""
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Images (*.jpg *.png *.webp)")
        if path:
            # Pass the selected path to handle_file_drop (no save dialog triggered)
            self.handle_file_drop(path)

    def select_output_file(self):
        """Opens file save dialog for output file using getSaveFileName."""
        current_out = self.output_entry.text()
        start_dir = os.path.dirname(current_out) if current_out else ""
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save As", 
            start_dir, 
            "JPEG (*.jpg);;PNG (*.png);;WebP (*.webp)",
            options=QFileDialog.DontConfirmOverwrite
        )
        if path:
            self.output_entry.setText(path)

    def toggle_ui(self, enable):
        self.compress_button.setEnabled(enable)
        self.drop_area.setEnabled(enable)
        if not enable:
            self.progress_bar.show()
            self.compress_button.setText("Compressing...")
        else:
            self.progress_bar.hide()
            self.compress_button.setText("Compress Image")

    def on_slider_changed(self):
        """Triggered when any slider changes - starts debounced timer"""
        self.estimation_timer.stop()
        self.estimation_timer.start(300)  # 300ms debounce
    
    def update_estimated_size(self):
        """Calculate and display estimated file size and resolution"""
        if self.original_size_mb <= 0:
            self.est_label.setText("Estimated Size: -")
            self.resolution_label.setText("New Resolution: -")
            return
        
        quality = self.quality_slider.value()
        resize = self.resize_slider.value()
        resize_ratio = resize / 100.0
        
        # Special case: if quality is 100 and resize is 100, Est. Size = Original Size
        if quality == 100 and resize == 100:
            estimated_size = self.original_size_mb
        else:
            # Formula: EstSize = OriginalSize * (Quality/100) * ((Resize/100)^2)
            estimated_size = self.original_size_mb * (quality / 100.0) * ((resize / 100.0) ** 2)
        
        self.est_label.setText(f"Estimated Size: {estimated_size:.2f} MB")
        
        # Update resolution display
        if self.original_width > 0 and self.original_height > 0:
            new_width = int(self.original_width * resize_ratio)
            new_height = int(self.original_height * resize_ratio)
            self.resolution_label.setText(f"New Resolution: {new_width} × {new_height} px")
        else:
            self.resolution_label.setText("New Resolution: -")
    
    def start_compression(self):
        try:
            quality = self.quality_slider.value()
            resize = self.resize_slider.value() / 100.0
            in_path = self.input_entry.text()
            out_path = self.output_entry.text()

            if not in_path or not os.path.exists(in_path):
                raise ValueError("Select an existing file!")
            if not out_path:
                raise ValueError("Specify a save path!")
            
            fmt = out_path.split(".")[-1].upper()
            if fmt == "JPG": fmt = "JPEG"

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        self.toggle_ui(False)
        self.worker = CompressionWorker(in_path, out_path, quality, fmt, resize)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, res: CompressionResult):
        self.toggle_ui(True)
        QMessageBox.information(self, "Done!", 
            f"✅ Success!\n\n"
            f"Size: {res.original_size_mb:.2f}MB ➝ {res.compressed_size_mb:.2f}MB\n"
            f"Savings: -{res.compression_ratio:.1f}%")

    def on_error(self, err_msg):
        self.toggle_ui(True)
        QMessageBox.critical(self, "Error", f"Failed to compress:\n{err_msg}")