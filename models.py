from dataclasses import dataclass
from typing import Tuple

@dataclass
class CompressionResult:
    original_size_mb: float
    compressed_size_mb: float
    compression_ratio: float
    original_resolution: Tuple[int, int]
    final_resolution: Tuple[int, int]
    output_path: str