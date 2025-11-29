import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import compress_image

class TestImageCompression(unittest.TestCase):
    
    # Мокаем и Image.open, и os.path.getsize (чтобы не лезть в файловую систему)
    @patch('os.path.getsize')
    @patch('PIL.Image.open')
    def test_compress_image_calls_save(self, mock_open, mock_getsize):
        # 1. Создаем наш мок картинки
        mock_img = MagicMock()
        
        # 2. Настраиваем Context Manager правильно!
        # Когда вызывается open(), он возвращает объект-контекст.
        # Когда у контекста вызывается __enter__, он возвращает нашу картинку.
        mock_open.return_value.__enter__.return_value = mock_img
        
        # 3. Настраиваем методы самой картинки, чтобы они возвращали self (для цепочек вызовов)
        mock_img.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        # 4. Настраиваем getsize, чтобы он возвращал фиктивный размер (например, 1024 байта)
        mock_getsize.return_value = 1024
        
        # --- ЗАПУСК ---
        input_path = "dummy.jpg"
        output_path = "dummy_compressed.jpg"
        quality = 85
        output_format = "JPEG"
        resize_ratio = 1.0 
        
        result, message = compress_image(input_path, output_path, quality, output_format, resize_ratio)
        
        # --- ПРОВЕРКИ ---
        
        # Проверяем, что картинка открывалась
        mock_open.assert_called_with(input_path)
        
        # Проверяем, что сохранение было вызвано
        mock_img.save.assert_called()
        
        # Проверяем, что функция успешно завершилась (Result == True)
        self.assertTrue(result, f"Функция вернула ошибку: {message}")

if __name__ == '__main__':
    unittest.main()