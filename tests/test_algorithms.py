import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем корневую папку в путь, чтобы видеть модули проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import compress_image

class TestImageCompression(unittest.TestCase):
    
    @patch('PIL.Image.open')
    def test_compress_image_calls_save(self, mock_open):
        """
        Тест проверяет, что функция сжатия открывает картинку и пытается её сохранить.
        Мы мокаем (имитируем) объект Image, чтобы не работать с реальными файлами.
        """
        # Настройка мока
        mock_img = MagicMock()
        mock_open.return_value = mock_img
        
        # Запуск функции
        input_path = "dummy.jpg"
        output_path = "dummy_compressed.jpg"
        quality = 85
        
        compress_image(input_path, output_path, quality)
        
        # Проверки (Assertions)
        mock_open.assert_called_with(input_path)  # Картинка открылась?
        mock_img.save.assert_called()             # Картинка сохранилась?
        
if __name__ == '__main__':
    unittest.main()