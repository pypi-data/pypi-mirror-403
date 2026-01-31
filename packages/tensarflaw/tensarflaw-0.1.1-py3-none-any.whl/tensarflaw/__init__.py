"""TensarFlaw - библиотека для работы с изображениями и TensorFlow"""

__version__ = "0.1.1"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Импортируем все функции напрямую в корневой модуль
from .load import (
    main,
    print_help,
    load11,
    load12,
    load31,
    load32,
    load41,
    load42,
    load51,
    load52
)

# Экспортируем их для удобного доступа
__all__ = [
    'main',
    'print_help',
    'load11',
    'load12', 
    'load31',
    'load32',
    'load41',
    'load42',
    'load51',
    'load52'
]