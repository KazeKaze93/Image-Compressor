import os
import sys
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet
from interface import ImageCompressorApp

if __name__ == "__main__":
    # Фикс для корректного отображения на HiDPI экранах (4K мониторы)
    if hasattr(sys, 'frozen'):
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    
    # Применяем магию (Dark Teal Theme)
    # invert_secondary=True делает акценты более яркими
    apply_stylesheet(app, theme='dark_teal.xml', invert_secondary=True)

    window = ImageCompressorApp()
    window.show()
    sys.exit(app.exec_())