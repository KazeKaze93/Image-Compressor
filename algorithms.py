import os
import shutil
from pathlib import Path
from PIL import Image
from models import CompressionResult

def get_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)

def compress_image(
    input_path: str, 
    output_path: str, 
    quality: int, 
    output_format: str, 
    resize_ratio: float
) -> CompressionResult:
    """
    Сжимает изображение с использованием продвинутых алгоритмов Pillow.
    Выбрасывает исключения при ошибках, вместо возврата кортежей.
    """
    
    # Валидация путей
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    try:
        with Image.open(input_path) as img:
            original_res = img.size
            original_size = get_size_mb(input_path)

            # 1. Ресайз (Lanczos - лучший фильтр для даунскейлинга)
            if resize_ratio < 1.0:
                new_width = int(original_res[0] * resize_ratio)
                new_height = int(original_res[1] * resize_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            final_res = img.size

            # 2. Сохранение с оптимизацией под формат
            save_params = {}

            if output_format.upper() in ["JPEG", "JPG"]:
                # Convert to RGB if needed
                if img.mode in ("RGBA", "P"): 
                    img = img.convert("RGB")
                
                # JPEG Optimization: subsampling=2 (4:2:0) if quality < 95, subsampling=0 if quality >= 95
                subsampling = 2 if quality < 95 else 0
                
                save_params.update({
                    "format": "JPEG",
                    "quality": quality,
                    "progressive": True,
                    "optimize": True,
                    "subsampling": subsampling
                })
                
            elif output_format.upper() == "WEBP":
                # method=6: самое медленное, но эффективное сжатие
                save_params.update({
                    "format": "WEBP",
                    "quality": quality,
                    "method": 6 
                })
                
            elif output_format.upper() == "PNG":
                # PNG - lossless, quality там нет. 
                # Если нужно сильное сжатие, уменьшаем цвета (Quantization)
                save_params["format"] = "PNG"
                # Если качество ниже 100, применяем адаптивное уменьшение цветов
                if quality < 100:
                    # Конвертируем качество 1-100 в количество цветов (2-256)
                    colors = max(2, int(256 * (quality / 100)))
                    img = img.quantize(colors=colors, method=2) # method 2 = FastOctree

            else:
                raise ValueError(f"Неподдерживаемый формат: {output_format}")

            # Сохраняем изображение в память для возможного пересохранения
            img_copy = img.copy()
            
            # Сохраняем
            img.save(output_path, **save_params)

            # SIZE GUARANTEE: Compare compressed_size with original_size
            compressed_size = get_size_mb(output_path)
            
            # FAILSAFE: If compressed_size > original_size, attempt recovery
            if compressed_size > original_size:
                if output_format.upper() in ["JPEG", "JPG"]:
                    # Attempt second save with quality=85 and subsampling=2
                    img_copy.save(output_path, format="JPEG", quality=85, optimize=True, progressive=True, subsampling=2)
                    compressed_size = get_size_mb(output_path)
                    
                    # If STILL larger, copy original to ensure best version
                    if compressed_size > original_size:
                        shutil.copy2(input_path, output_path)
                        compressed_size = original_size
                elif output_format.upper() == "WEBP":
                    # For WebP, try quality=80
                    img_copy.save(output_path, format="WEBP", quality=80, method=6)
                    compressed_size = get_size_mb(output_path)
                    
                    if compressed_size > original_size:
                        shutil.copy2(input_path, output_path)
                        compressed_size = original_size
                else:
                    # For PNG and other formats, copy original
                    shutil.copy2(input_path, output_path)
                    compressed_size = original_size
            
            return CompressionResult(
                original_size_mb=original_size,
                compressed_size_mb=compressed_size,
                compression_ratio=((original_size - compressed_size) / original_size) * 100,
                original_resolution=original_res,
                final_resolution=final_res,
                output_path=output_path
            )

    except Exception as e:
        # Пробрасываем ошибку наверх, интерфейс сам решит, как её показать
        raise RuntimeError(f"Ошибка при обработке изображения: {str(e)}")