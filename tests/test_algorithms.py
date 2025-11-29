import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import compress_image

class TestImageCompression(unittest.TestCase):
    
    @patch('PIL.Image.open')
    def test_compress_image_calls_save(self, mock_open):
        # Настройка мока
        mock_img = MagicMock()
        mock_open.return_value = mock_img
        
        # Запуск функции с 5 аргументами!
        input_path = "dummy.jpg"
        output_path = "dummy_compressed.jpg"
        quality = 85
        output_format = "JPEG"  # <-- Добавили
        resize_ratio = 1.0      # <-- Добавили (100% размер)
        
        compress_image(input_path, output_path, quality, output_format, resize_ratio)
        
        # Проверки
        mock_open.assert_called_with(input_path)
        # Проверяем, что save был вызван (аргументы save могут отличаться, нам важен сам факт сохранения)
        mock_img.save.assert_called()
        
if __name__ == '__main__':
    unittest.main()