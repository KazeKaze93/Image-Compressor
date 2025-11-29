import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import compress_image

class TestImageCompression(unittest.TestCase):
    
    @patch('PIL.Image.open')
    def test_compress_image_calls_save(self, mock_open):
        # --- НАСТРОЙКА МОКА (FIX) ---
        mock_img = MagicMock()
        
        # 1. Если код использует 'with Image.open(...) as img', 
        # то img берется из метода __enter__. Настраиваем его:
        mock_open.return_value.__enter__.return_value = mock_img
        
        # 2. На случай, если код не использует with, а просто img = open(...)
        mock_open.return_value = mock_img

        # 3. Если код делает img = img.convert(...) или img.resize(...),
        # PIL обычно возвращает новый объект. Мы заставляем мок возвращать сам себя,
        # чтобы цепочка вызовов не прерывалась.
        mock_img.convert.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        # --- ЗАПУСК ---
        input_path = "dummy.jpg"
        output_path = "dummy_compressed.jpg"
        quality = 85
        output_format = "JPEG"
        resize_ratio = 1.0 
        
        compress_image(input_path, output_path, quality, output_format, resize_ratio)
        
        # --- ПРОВЕРКИ ---
        mock_open.assert_called_with(input_path)
        mock_img.save.assert_called()
        
if __name__ == '__main__':
    unittest.main()