import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from algorithms import compress_image
# Импортируем исключение, если нужно, или просто ловим Exception

class TestImageCompression(unittest.TestCase):
    
    @patch('os.path.exists') # Мокаем проверку пути
    @patch('os.path.getsize')
    @patch('PIL.Image.open')
    def test_compress_jpeg_flow(self, mock_open, mock_getsize, mock_exists):
        # Setup
        mock_exists.return_value = True # Файл существует
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img
        mock_img.convert.return_value = mock_img # На случай конвертации в RGB
        mock_img.resize.return_value = mock_img
        
        # Заставляем вернуть режим RGB (чтобы не триггерить конвертацию P->RGB, хотя это не критично)
        mock_img.mode = 'RGB' 
        
        mock_getsize.return_value = 2048 * 1024 # 2 MB

        # Action
        result = compress_image(
            input_path="test.jpg",
            output_path="out.jpg",
            quality=80,
            output_format="JPEG",
            resize_ratio=1.0
        )

        # Assert
        mock_open.assert_called_once()
        mock_img.save.assert_called()
        
        # Проверяем, что передали оптимизацию и progressive
        _, kwargs = mock_img.save.call_args
        self.assertEqual(kwargs['format'], 'JPEG')
        self.assertTrue(kwargs['optimize'])
        self.assertTrue(kwargs['progressive'])

        # Проверяем, что вернулся объект с данными
        self.assertAlmostEqual(result.original_size_mb, 2.0)

if __name__ == '__main__':
    unittest.main()