"""
Adaptateurs pour intégrer les modules C/C++ optimisés dans les détecteurs.
Utilise les optimisations natives quand disponibles, fallback sur Python sinon.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional

# Essayer de charger les modules C/C++ optimisés
try:
    from .cpp import get_image_filters, get_geometry_utils
    HAS_CPP_MODULES = True
except (ImportError, FileNotFoundError):
    HAS_CPP_MODULES = False


class OptimizedImageFilters:
    """Interface unifiée pour les filtres d'image avec fallback automatique."""
    
    def __init__(self):
        self.use_cpp = HAS_CPP_MODULES
        if HAS_CPP_MODULES:
            self.cpp_filters = get_image_filters()
    
    def gaussian_blur(self, image: np.ndarray, kernel_size: int = 5, 
                     sigma: float = 1.0) -> np.ndarray:
        """Gaussian blur avec accélération C/C++ si disponible."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                if image.shape[2] == 3:  # BGR
                    return self.cpp_filters.gaussian_blur(image, kernel_size, sigma)
            except (AttributeError, TypeError):
                pass
        
        # Fallback Python
        import cv2
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    def bgr_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Conversion BGR -> Grayscale optimisée."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_filters.bgr_to_grayscale(image)
            except (AttributeError, TypeError):
                pass
        
        import cv2
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def canny_edges(self, image: np.ndarray, low: float = 50, 
                   high: float = 150) -> np.ndarray:
        """Détection Canny optimisée."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_filters.canny_edges(image, low, high)
            except (AttributeError, TypeError):
                pass
        
        import cv2
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(image, int(low), int(high))


class OptimizedGeometryUtils:
    """Interface unifiée pour calculs géométriques avec fallback automatique."""
    
    def __init__(self):
        self.use_cpp = HAS_CPP_MODULES
        if HAS_CPP_MODULES:
            self.cpp_geom = get_geometry_utils()
        else:
            from .. import math_utils
            self.math = math_utils
    
    def euclidean_distance(self, x1: float, y1: float, 
                          x2: float, y2: float) -> float:
        """Distance euclidienne ultra-rapide."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.euclidean_distance(x1, y1, x2, y2)
            except (AttributeError, TypeError):
                pass
        
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def manhattan_distance(self, x1: float, y1: float, 
                          x2: float, y2: float) -> float:
        """Distance de Manhattan."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.manhattan_distance(x1, y1, x2, y2)
            except (AttributeError, TypeError):
                pass
        
        return abs(x2 - x1) + abs(y2 - y1)
    
    def polygon_area(self, polygon: List[Tuple[float, float]]) -> float:
        """Calcule l'aire d'un polygone."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.polygon_area(polygon)
            except (AttributeError, TypeError):
                pass
        
        # Fallback Python
        area = 0.0
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            area += (x1 * y2 - x2 * y1)
        return abs(area) / 2.0
    
    def polygon_perimeter(self, polygon: List[Tuple[float, float]]) -> float:
        """Calcule le périmètre d'un polygone."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.polygon_perimeter(polygon)
            except (AttributeError, TypeError):
                pass
        
        # Fallback Python
        perimeter = 0.0
        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]
            perimeter += self.euclidean_distance(p1[0], p1[1], p2[0], p2[1])
        return perimeter
    
    def is_rectangle(self, polygon: List[Tuple[float, float]], 
                    tolerance: float = 0.1) -> bool:
        """Détecte si une forme est un rectangle."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.is_rectangle(polygon, tolerance)
            except (AttributeError, TypeError):
                pass
        
        if len(polygon) != 4:
            return False
        
        # Vérification Python fallback
        angles_ok = 0
        for i in range(4):
            p1 = np.array(polygon[i])
            p2 = np.array(polygon[(i + 1) % 4])
            p3 = np.array(polygon[(i + 2) % 4])
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            dot = np.dot(v1, v2)
            len1, len2 = np.linalg.norm(v1), np.linalg.norm(v2)
            
            if len1 > 0 and len2 > 0:
                cos_angle = dot / (len1 * len2)
                angle = np.arccos(np.clip(cos_angle, -1, 1))
                
                if abs(angle - np.pi / 2) < tolerance:
                    angles_ok += 1
        
        return angles_ok == 4
    
    def is_circle(self, polygon: List[Tuple[float, float]], 
                 circularity_threshold: float = 0.8) -> bool:
        """Détecte si une forme est un cercle."""
        if HAS_CPP_MODULES and self.use_cpp:
            try:
                return self.cpp_geom.is_circle(polygon, circularity_threshold)
            except (AttributeError, TypeError):
                pass
        
        area = self.polygon_area(polygon)
        perimeter = self.polygon_perimeter(polygon)
        
        if perimeter == 0:
            return False
        
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        return circularity > circularity_threshold


# Singletons globaux pour performance
_image_filters = None
_geometry_utils = None


def get_optimized_filters() -> OptimizedImageFilters:
    """Obtient l'instance singleton des filtres optimisés."""
    global _image_filters
    if _image_filters is None:
        _image_filters = OptimizedImageFilters()
    return _image_filters


def get_optimized_geometry() -> OptimizedGeometryUtils:
    """Obtient l'instance singleton de géométrie optimisée."""
    global _geometry_utils
    if _geometry_utils is None:
        _geometry_utils = OptimizedGeometryUtils()
    return _geometry_utils
