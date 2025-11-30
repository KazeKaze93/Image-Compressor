import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from algorithms import compress_image
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
        self.setText("📂 Перетащите изображение сюда\nили кликните для выбора")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        # Стилизация зоны перетаскивания
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #263238;
                color: #ccc;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #00bcd4;
                color: #fff;
                background-color: #37474f;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # Проверяем расширение
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Ошибка", "Поддерживаются только изображения (JPG, PNG, WEBP)")

    def mousePressEvent(self, event):
        # Клик по зоне тоже открывает диалог
        if event.button() == Qt.LeftButton:
            self.file_dropped.emit("CLICK")

# --- MAIN WINDOW ---
class ImageCompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Compressor Pro")
        self.resize(600, 450) 
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(15)

        self.setup_ui()

    def setup_ui(self):
        # 1. Drag & Drop Area
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self.handle_file_drop)
        self.layout.addWidget(self.drop_area)

        # 2. Paths Group
        path_group = QGroupBox("Пути к файлам")
        path_layout = QVBoxLayout()
        
        self.input_entry = self._create_row(path_layout, "Вход:", read_only=True)
        self.output_entry = self._create_row(path_layout, "Выход:")
        
        # Кнопка выбора выходного пути
        self.btn_save = QPushButton("Выбрать место сохранения...")
        self.btn_save.clicked.connect(self.select_output_file)
        path_layout.addWidget(self.btn_save)
        
        path_group.setLayout(path_layout)
        self.layout.addWidget(path_group)

        # 3. Settings Group
        settings_group = QGroupBox("Настройки сжатия")
        settings_layout = QHBoxLayout()
        
        self.quality_entry = self._create_param(settings_layout, "Качество (1-100):", "85")
        self.resize_entry = self._create_param(settings_layout, "Размер (%):", "100")
        
        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        # 4. Progress & Action
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Infinite loading style
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        self.compress_button = QPushButton("🚀 СЖАТЬ ИЗОБРАЖЕНИЕ")
        self.compress_button.setMinimumHeight(45)
        self.compress_button.setCursor(Qt.PointingHandCursor)
        self.compress_button.clicked.connect(self.start_compression)
        
        # Стилизация главной кнопки
        self.compress_button.setStyleSheet("""
            QPushButton {
                background-color: #00bcd4;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #00acc1; }
            QPushButton:disabled { background-color: #555; }
        """)
        self.layout.addWidget(self.compress_button)

        self.layout.addStretch() # Push everything up

    def _create_row(self, parent_layout, label_text, read_only=False):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(50)
        entry = QLineEdit()
        entry.setReadOnly(read_only)
        entry.setPlaceholderText("Путь к файлу...")
        row.addWidget(lbl)
        row.addWidget(entry)
        parent_layout.addLayout(row)
        return entry

    def _create_param(self, parent_layout, label_text, default_val):
        container = QVBoxLayout()
        lbl = QLabel(label_text)
        entry = QLineEdit(default_val)
        entry.setAlignment(Qt.AlignCenter)
        container.addWidget(lbl)
        container.addWidget(entry)
        parent_layout.addLayout(container)
        return entry

    # --- HANDLERS ---
    def handle_file_drop(self, path):
        if path == "CLICK":
            self.select_input_file()
        else:
            self.input_entry.setText(path)
            # Автоматически генерируем путь выхода
            folder, filename = os.path.split(path)
            name, ext = os.path.splitext(filename)
            new_name = f"{name}_compressed{ext}"
            self.output_entry.setText(os.path.join(folder, new_name))

    def select_input_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Images (*.jpg *.png *.webp)")
        if path: self.handle_file_drop(path)

    def select_output_file(self):
        current_out = self.output_entry.text()
        start_dir = os.path.dirname(current_out) if current_out else ""
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", start_dir, "JPEG (*.jpg);;PNG (*.png);;WebP (*.webp)")
        if path: self.output_entry.setText(path)

    def toggle_ui(self, enable):
        self.compress_button.setEnabled(enable)
        self.drop_area.setEnabled(enable)
        if not enable:
            self.progress_bar.show()
            self.compress_button.setText("Сжатие...")
        else:
            self.progress_bar.hide()
            self.compress_button.setText("🚀 СЖАТЬ ИЗОБРАЖЕНИЕ")

    def start_compression(self):
        try:
            quality = int(self.quality_entry.text())
            resize = int(self.resize_entry.text()) / 100.0
            in_path = self.input_entry.text()
            out_path = self.output_entry.text()

            if not in_path or not os.path.exists(in_path):
                raise ValueError("Выберите существующий файл!")
            if not out_path:
                raise ValueError("Укажите путь для сохранения!")
            
            fmt = out_path.split(".")[-1].upper()
            if fmt == "JPG": fmt = "JPEG"

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            return

        self.toggle_ui(False)
        self.worker = CompressionWorker(in_path, out_path, quality, fmt, resize)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, res: CompressionResult):
        self.toggle_ui(True)
        QMessageBox.information(self, "Готово!", 
            f"✅ Успешно!\n\n"
            f"Размер: {res.original_size_mb:.2f}MB ➝ {res.compressed_size_mb:.2f}MB\n"
            f"Выгода: -{res.compression_ratio:.1f}%")

    def on_error(self, err_msg):
        self.toggle_ui(True)
        QMessageBox.critical(self, "Ошибка", f"Не удалось сжать:\n{err_msg}")