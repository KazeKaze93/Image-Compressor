import sys
import traceback
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from algorithms import compress_image
from models import CompressionResult

# --- WORKER THREAD ---
# Выносим тяжелую задачу в отдельный поток
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
                self.input_path, 
                self.output_path, 
                self.quality, 
                self.output_format, 
                self.resize_ratio
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# --- MAIN WINDOW ---
class ImageCompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Compressor Pro")
        self.setFixedSize(500, 200) # Чуть увеличил высоту под прогресс-бар

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()

    def setup_ui(self):
        # Input
        self.input_entry = self._create_file_selector("Входной файл:", self.select_input_file)
        # Output
        self.output_entry = self._create_file_selector("Выходной файл:", self.select_output_file)
        
        # Params
        self.quality_entry = QLineEdit("85")
        self.resize_entry = QLineEdit("100")
        self.setup_params_row()

        # Progress Bar (скрыт по умолчанию)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Бесконечный спиннер
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # Button
        self.compress_button = QPushButton("Сжать (Start)")
        self.compress_button.clicked.connect(self.start_compression)
        self.layout.addWidget(self.compress_button)

    def _create_file_selector(self, label_text, handler):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        entry = QLineEdit()
        btn = QPushButton("...")
        btn.setFixedWidth(40)
        btn.clicked.connect(handler)
        layout.addWidget(entry)
        layout.addWidget(btn)
        self.layout.addLayout(layout)
        return entry

    def setup_params_row(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Качество (%):"))
        self.quality_entry.setFixedWidth(50)
        layout.addWidget(self.quality_entry)
        
        layout.addSpacing(20)
        
        layout.addWidget(QLabel("Ресайз (%):"))
        self.resize_entry.setFixedWidth(50)
        layout.addWidget(self.resize_entry)
        layout.addStretch()
        self.layout.addLayout(layout)

    def select_input_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.jpg *.png *.webp)")
        if path: self.input_entry.setText(path)

    def select_output_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "JPEG (*.jpg);;PNG (*.png);;WebP (*.webp)")
        if path: self.output_entry.setText(path)

    def toggle_ui(self, enable):
        """Блокирует интерфейс во время работы"""
        self.compress_button.setEnabled(enable)
        self.input_entry.setEnabled(enable)
        if not enable:
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def start_compression(self):
        # Валидация простая, UI не должен сильно думать
        try:
            quality = int(self.quality_entry.text())
            resize = int(self.resize_entry.text()) / 100.0
            in_path = self.input_entry.text()
            out_path = self.output_entry.text()
            
            if not in_path or not out_path:
                raise ValueError("Выберите файлы")
            
            fmt = out_path.split(".")[-1].upper()
            if fmt == "JPG": fmt = "JPEG"

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        # Запуск потока
        self.toggle_ui(False)
        self.worker = CompressionWorker(in_path, out_path, quality, fmt, resize)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, res: CompressionResult):
        self.toggle_ui(True)
        msg = (f"Успех!\n"
               f"Размер: {res.original_size_mb:.2f}MB -> {res.compressed_size_mb:.2f}MB\n"
               f"Сжато на: {res.compression_ratio:.1f}%")
        QMessageBox.information(self, "Done", msg)

    def on_error(self, err_msg):
        self.toggle_ui(True)
        QMessageBox.critical(self, "Error", err_msg)