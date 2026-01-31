"""
Module d'optimisation et gestion de la complexité des images.
Adapte la résolution et les paramètres selon la complexité détectée.
"""

import cv2
import numpy as np
from typing import Tuple, Dict
from enum import Enum


class ImageComplexity(Enum):
    """Niveaux de complexité d'image."""
    LOW = "low"  # Simple, peu de détails
    MEDIUM = "medium"  # Complexité modérée
    HIGH = "high"  # Très complexe, beaucoup de détails


class OptimizationProfile(Enum):
    """Profils d'optimisation."""
    SPEED = "speed"  # Priorité à la vitesse
    QUALITY = "quality"  # Priorité à la qualité
    BALANCED = "balanced"  # Équilibre vitesse/qualité


class ImageOptimizer:
    """Optimise les images selon leur complexité."""
    
    def __init__(self, profile: str = "balanced"):
        """
        Initialise l'optimiseur.
        
        Args:
            profile: "speed", "quality" ou "balanced"
        """
        self.profile = OptimizationProfile(profile)
        
        # Configuration par profil
        self.configs = {
            OptimizationProfile.SPEED: {
                'max_width': 640,
                'max_height': 480,
                'jpeg_quality': 70,
                'blur_kernel': (3, 3),
                'canny_threshold1': 50,
                'canny_threshold2': 150,
            },
            OptimizationProfile.QUALITY: {
                'max_width': 1920,
                'max_height': 1440,
                'jpeg_quality': 95,
                'blur_kernel': (7, 7),
                'canny_threshold1': 30,
                'canny_threshold2': 100,
            },
            OptimizationProfile.BALANCED: {
                'max_width': 1024,
                'max_height': 768,
                'jpeg_quality': 85,
                'blur_kernel': (5, 5),
                'canny_threshold1': 40,
                'canny_threshold2': 120,
            },
        }
    
    def detect_complexity(self, image: np.ndarray) -> ImageComplexity:
        """
        Détecte la complexité de l'image.
        
        Args:
            image: Image en format numpy array
        
        Returns:
            Niveau de complexité
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Laplacian pour détecter les variations
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Nombre de pixels uniques (entropie simple)
        unique_pixels = len(np.unique(gray))
        entropy_ratio = unique_pixels / (gray.shape[0] * gray.shape[1])
        
        # Seuils
        if variance < 100 or entropy_ratio < 0.1:
            return ImageComplexity.LOW
        elif variance > 500 or entropy_ratio > 0.5:
            return ImageComplexity.HIGH
        else:
            return ImageComplexity.MEDIUM
    
    def resize_for_optimization(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Redimensionne l'image selon le profil.
        
        Args:
            image: Image originale
        
        Returns:
            (Image redimensionnée, facteur de mise à l'échelle)
        """
        config = self.configs[self.profile]
        max_width = config['max_width']
        max_height = config['max_height']
        
        height, width = image.shape[:2]
        
        # Calculer le facteur de redimensionnement
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            return resized, scale
        
        return image, 1.0
    
    def get_optimized_params(self, image: np.ndarray) -> Dict:
        """
        Obtient les paramètres optimisés selon la complexité.
        
        Args:
            image: Image
        
        Returns:
            Dictionnaire de paramètres optimisés
        """
        complexity = self.detect_complexity(image)
        config = self.configs[self.profile]
        
        # Ajuster les paramètres selon la complexité
        if complexity == ImageComplexity.LOW:
            # Image simple: paramètres agressifs pour plus de vitesse
            return {
                'blur_kernel': (3, 3),
                'canny_threshold1': 60,
                'canny_threshold2': 180,
                'min_contour_area': 100,
                'hough_dp': 1.5,
                'hough_param1': 120,
                'hough_param2': 40,
            }
        elif complexity == ImageComplexity.HIGH:
            # Image complexe: paramètres conservateurs pour meilleure qualité
            return {
                'blur_kernel': config['blur_kernel'],
                'canny_threshold1': config['canny_threshold1'],
                'canny_threshold2': config['canny_threshold2'],
                'min_contour_area': 50,
                'hough_dp': 1.0,
                'hough_param1': 100,
                'hough_param2': 30,
            }
        else:
            # Équilibre
            return {
                'blur_kernel': config['blur_kernel'],
                'canny_threshold1': config['canny_threshold1'],
                'canny_threshold2': config['canny_threshold2'],
                'min_contour_area': 75,
                'hough_dp': 1.0,
                'hough_param1': 100,
                'hough_param2': 30,
            }
    
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Prétraite l'image (redimensionnement + paramètres optimisés).
        
        Args:
            image: Image originale
        
        Returns:
            (Image prétraitée, informations de transformation)
        """
        # Redimensionner
        resized, scale = self.resize_for_optimization(image)
        
        # Obtenir les paramètres
        params = self.get_optimized_params(resized)
        
        return resized, {
            'scale': scale,
            'params': params,
            'complexity': self.detect_complexity(resized).value
        }


class FastImageProcessor:
    """Traitement rapide avec cache et optimisations."""
    
    def __init__(self, profile: str = "balanced", enable_cache: bool = True):
        """
        Initialise le processeur rapide.
        
        Args:
            profile: Profil d'optimisation
            enable_cache: Activer le cache des résultats
        """
        self.optimizer = ImageOptimizer(profile)
        self.cache = {} if enable_cache else None
        self.cache_enabled = enable_cache
    
    def _get_cache_key(self, image_data: bytes, operation: str) -> str:
        """Génère une clé de cache."""
        import hashlib
        h = hashlib.md5(image_data).hexdigest()
        return f"{operation}_{h}"
    
    def clear_cache(self):
        """Vide le cache."""
        if self.cache is not None:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Retourne les statistiques du cache."""
        if self.cache is None:
            return {'enabled': False}
        return {
            'enabled': True,
            'size': len(self.cache),
            'entries': list(self.cache.keys())
        }


__all__ = [
    'ImageOptimizer',
    'FastImageProcessor',
    'ImageComplexity',
    'OptimizationProfile'
]
