'''Cryptanalysis swiss army knife'''

__version__ = "0.7.0"

try:
    from .conv import B, load_bytes
except ImportError:
    pass  # this happens when importing from setup.py
