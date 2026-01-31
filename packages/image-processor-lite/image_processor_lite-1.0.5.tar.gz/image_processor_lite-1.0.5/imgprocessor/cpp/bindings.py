"""
Wrappers Python pour les modules C/C++ optimisés.
Utilise ctypes pour interfacer avec les librairies compilées.
"""

import ctypes
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import platform
import logging

logger = logging.getLogger(__name__)

# Déterminer le chemin vers les librairies compilées
LIB_PATH = Path(__file__).parent.parent / "cpp" / "build"

def get_library_name(lib_name: str) -> str:
    """Obtient le nom de fichier approprié selon le système d'exploitation."""
    system = platform.system()
    
    if system == "Windows":
        return f"{lib_name}.dll"
    elif system == "Darwin":  # macOS
        return f"lib{lib_name}.dylib"
    else:  # Linux
        return f"lib{lib_name}.so"

def load_library(lib_name: str) -> ctypes.CDLL:
    """Charge une librairie compilée."""
    lib_file = LIB_PATH / get_library_name(lib_name)
    
    if not lib_file.exists():
        raise FileNotFoundError(f"Librairie non trouvée: {lib_file}")
    
    return ctypes.CDLL(str(lib_file))

# ============================================================================
# IMAGE FILTERS - Module image_filters.cpp
# ============================================================================

class ImageFilters:
    """Wrappers C/C++ pour les filtres d'image critiques."""
    
    def __init__(self):
        try:
            self.lib = load_library("image_filters")
            self._setup_functions()
        except FileNotFoundError:
            self.lib = None
    
    def _setup_functions(self):
        """Configure les signatures de fonctions C/C++."""
        if not self.lib:
            return
        
        # gaussian_blur
        self.lib.gaussian_blur.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),  # image_data
            ctypes.c_int,                     # width
            ctypes.c_int,                     # height
            ctypes.c_int,                     # channels
            ctypes.c_int,                     # kernel_size
            ctypes.c_float,                   # sigma
            ctypes.POINTER(ctypes.c_ubyte)   # output
        ]
        self.lib.gaussian_blur.restype = None
        
        # bgr_to_grayscale
        self.lib.bgr_to_grayscale.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_ubyte)
        ]
        self.lib.bgr_to_grayscale.restype = None
        
        # canny_edges
        self.lib.canny_edges.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_float,
            ctypes.c_float,
            ctypes.POINTER(ctypes.c_ubyte)
        ]
        self.lib.canny_edges.restype = None
    
    def gaussian_blur(self, image: np.ndarray, kernel_size: int = 5, 
                     sigma: float = 1.0) -> np.ndarray:
        """
        Applique un filtre Gaussien.
        Version C/C++ optimisée (2-5x plus rapide que Python).
        """
        if not self.lib:
            return self._gaussian_blur_python(image, kernel_size, sigma)
        
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Image doit être BGR 3 canaux")
        
        height, width, channels = image.shape
        image_c = np.ascontiguousarray(image, dtype=np.uint8)
        output = np.zeros((height, width, channels), dtype=np.uint8)
        
        try:
            self.lib.gaussian_blur(
                image_c.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),
                width, height, channels,
                kernel_size, sigma,
                output.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            )
            return output
        except Exception as e:
            logger.error(f"C/C++ error: {e}, using Python fallback")
            return self._gaussian_blur_python(image, kernel_size, sigma)
    
    def _gaussian_blur_python(self, image: np.ndarray, kernel_size: int, 
                             sigma: float) -> np.ndarray:
        """Implémentation Python fallback."""
        import cv2
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    def bgr_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convertit BGR en niveaux de gris (optimisé C)."""
        if not self.lib:
            return self._bgr_to_grayscale_python(image)
        
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Image doit être BGR 3 canaux")
        
        height, width = image.shape[:2]
        image_c = np.ascontiguousarray(image, dtype=np.uint8)
        output = np.zeros((height, width), dtype=np.uint8)
        
        try:
            self.lib.bgr_to_grayscale(
                image_c.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),
                width, height,
                output.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            )
            return output
        except Exception as e:
            logger.error(f"C/C++ error: {e}")
            return self._bgr_to_grayscale_python(image)
    
    def _bgr_to_grayscale_python(self, image: np.ndarray) -> np.ndarray:
        """Implémentation Python fallback."""
        import cv2
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def canny_edges(self, image: np.ndarray, low_threshold: float = 50.0,
                   high_threshold: float = 150.0) -> np.ndarray:
        """Détecte les contours avec Canny (optimisé C/C++)."""
        if not self.lib:
            return self._canny_edges_python(image, low_threshold, high_threshold)
        
        if len(image.shape) == 3:
            image = self.bgr_to_grayscale(image)
        
        height, width = image.shape
        image_c = np.ascontiguousarray(image, dtype=np.uint8)
        output = np.zeros((height, width), dtype=np.uint8)
        
        try:
            self.lib.canny_edges(
                image_c.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)),
                width, height,
                low_threshold, high_threshold,
                output.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            )
            return output
        except Exception as e:
            logger.error(f"C/C++ error: {e}")
            return self._canny_edges_python(image, low_threshold, high_threshold)
    
    def _canny_edges_python(self, image: np.ndarray, low: float, 
                           high: float) -> np.ndarray:
        """Implémentation Python fallback."""
        import cv2
        return cv2.Canny(image, int(low), int(high))


# ============================================================================
# GEOMETRY UTILS - Module geometry_utils.cpp
# ============================================================================

class GeometryUtils:
    """Wrappers C/C++ pour calculs géométriques critiques."""
    
    def __init__(self):
        try:
            self.lib = load_library("geometry_utils")
            self._setup_functions()
        except FileNotFoundError:
            self.lib = None
    
    def _setup_functions(self):
        """Configure les signatures de fonctions C/C++."""
        if not self.lib:
            return
        
        # euclidean_distance
        self.lib.euclidean_distance.argtypes = [
            ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float
        ]
        self.lib.euclidean_distance.restype = ctypes.c_float
        
        # manhattan_distance
        self.lib.manhattan_distance.argtypes = [
            ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float
        ]
        self.lib.manhattan_distance.restype = ctypes.c_float
        
        # polygon_area
        self.lib.polygon_area.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int
        ]
        self.lib.polygon_area.restype = ctypes.c_float
        
        # polygon_perimeter
        self.lib.polygon_perimeter.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int
        ]
        self.lib.polygon_perimeter.restype = ctypes.c_float
        
        # is_rectangle
        self.lib.is_rectangle.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int,
            ctypes.c_float
        ]
        self.lib.is_rectangle.restype = ctypes.c_int
        
        # is_circle
        self.lib.is_circle.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_int,
            ctypes.c_float
        ]
        self.lib.is_circle.restype = ctypes.c_int
    
    def euclidean_distance(self, x1: float, y1: float, 
                          x2: float, y2: float) -> float:
        """Distance euclidienne ultra-rapide (optimisée C)."""
        if not self.lib:
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        try:
            return self.lib.euclidean_distance(
                ctypes.c_float(x1), ctypes.c_float(y1),
                ctypes.c_float(x2), ctypes.c_float(y2)
            )
        except Exception as e:
            logger.error(f"C/C++ error: {e}")
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def manhattan_distance(self, x1: float, y1: float, 
                          x2: float, y2: float) -> float:
        """Distance de Manhattan optimisée."""
        if not self.lib:
            return abs(x2 - x1) + abs(y2 - y1)
        
        try:
            return self.lib.manhattan_distance(
                ctypes.c_float(x1), ctypes.c_float(y1),
                ctypes.c_float(x2), ctypes.c_float(y2)
            )
        except Exception as e:
            return abs(x2 - x1) + abs(y2 - y1)
    
    def polygon_area(self, polygon: List[Tuple[float, float]]) -> float:
        """Calcule l'aire d'un polygone (optimisée C)."""
        if not self.lib:
            return self._polygon_area_python(polygon)
        
        # Convertir polygone en tableau float
        poly_array = np.array(polygon, dtype=np.float32).flatten()
        
        try:
            return self.lib.polygon_area(
                poly_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                len(poly_array)
            )
        except Exception as e:
            return self._polygon_area_python(polygon)
    
    def _polygon_area_python(self, polygon: List[Tuple[float, float]]) -> float:
        """Implémentation Python fallback (Shoelace)."""
        area = 0.0
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            area += (x1 * y2 - x2 * y1)
        return abs(area) / 2.0
    
    def polygon_perimeter(self, polygon: List[Tuple[float, float]]) -> float:
        """Calcule le périmètre d'un polygone."""
        if not self.lib:
            return self._polygon_perimeter_python(polygon)
        
        poly_array = np.array(polygon, dtype=np.float32).flatten()
        
        try:
            return self.lib.polygon_perimeter(
                poly_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                len(poly_array)
            )
        except Exception as e:
            return self._polygon_perimeter_python(polygon)
    
    def _polygon_perimeter_python(self, polygon: List[Tuple[float, float]]) -> float:
        """Implémentation Python fallback."""
        perimeter = 0.0
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            perimeter += self.euclidean_distance(x1, y1, x2, y2)
        return perimeter
    
    def is_rectangle(self, polygon: List[Tuple[float, float]], 
                    angle_tolerance: float = 0.1) -> bool:
        """Détecte si une forme est un rectangle."""
        if not self.lib or len(polygon) != 4:
            return False
        
        poly_array = np.array(polygon, dtype=np.float32).flatten()
        
        try:
            result = self.lib.is_rectangle(
                poly_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                len(poly_array),
                angle_tolerance
            )
            return bool(result)
        except Exception as e:
            return False
    
    def is_circle(self, polygon: List[Tuple[float, float]], 
                 circularity_threshold: float = 0.8) -> bool:
        """Détecte si une forme est un cercle."""
        if not self.lib:
            return False
        
        poly_array = np.array(polygon, dtype=np.float32).flatten()
        
        try:
            result = self.lib.is_circle(
                poly_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                len(poly_array),
                circularity_threshold
            )
            return bool(result)
        except Exception as e:
            return False


# ============================================================================
# SINGLETONS GLOBAUX
# ============================================================================

_image_filters = None
_geometry_utils = None

def get_image_filters() -> ImageFilters:
    """Obtient l'instance singleton ImageFilters."""
    global _image_filters
    if _image_filters is None:
        _image_filters = ImageFilters()
    return _image_filters

def get_geometry_utils() -> GeometryUtils:
    """Obtient l'instance singleton GeometryUtils."""
    global _geometry_utils
    if _geometry_utils is None:
        _geometry_utils = GeometryUtils()
    return _geometry_utils
