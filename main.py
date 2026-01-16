import os
import sys
from PyQt5.QtWidgets import QApplication
from interface import ImageCompressorApp

if __name__ == "__main__":
    # Фикс для корректного отображения на HiDPI экранах (4K мониторы)
    if hasattr(sys, 'frozen'):
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    
    # Custom dark theme is applied in ImageCompressorApp.apply_stylesheet()

    window = ImageCompressorApp()
    window.show()
    sys.exit(app.exec_())