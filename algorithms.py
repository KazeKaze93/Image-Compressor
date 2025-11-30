import os
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
            save_params = {
                "optimize": True,
            }

            if output_format.upper() in ["JPEG", "JPG"]:
                # Progressive: лучше для веба. Subsampling 0: сохраняет цветовые детали.
                if img.mode in ("RGBA", "P"): 
                    img = img.convert("RGB")
                save_params.update({
                    "format": "JPEG",
                    "quality": quality,
                    "progressive": True,
                    "subsampling": 0 
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

            # Сохраняем
            img.save(output_path, **save_params)

            # Результат
            compressed_size = get_size_mb(output_path)
            
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