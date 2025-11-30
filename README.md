![Python CI](https://github.com/KazeKaze93/Image-Compressor/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 📸 Image Compressor Pro

A modern, high-performance desktop application for image compression. Built with Python, PyQt5, and advanced Pillow algorithms.

**[🇷🇺 Читать на русском](#-описание-на-русском)**

---

## 🚀 Features
* **Smart Compression:** Reduces file size while maintaining visual quality.
* **Format Support:** JPEG, PNG, WebP.
* **Drag & Drop:** Simply drag your images into the app.
* **Advanced Algorithms:** Uses Lanczos resampling and format-specific optimizations.
* **Modern UI:** Dark theme included.

## 📥 Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/KazeKaze93/Image-Compressor.git](https://github.com/KazeKaze93/Image-Compressor.git)
    cd Image-Compressor
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    python main.py
    ```

## 📦 Build EXE (Windows)
To create a standalone executable file:
```bash
python -m PyInstaller --noconfirm --onefile --windowed --name "CompressorPro" --collect-all qt_material --collect-all PyQt5 main.py
