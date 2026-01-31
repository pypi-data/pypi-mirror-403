"""
image-processor-lite - Package modulaire de traitement et d'analyse d'images.

Un package permettant d'effectuer indépendamment les opérations suivantes:
- Détection et extraction de texte (OCR)
- Détection de formes géométriques
- Mesure de distances entre objets
- Analyse visuelle (luminosité, contraste, teinte)

Chaque module peut être activé/désactivé indépendamment selon les besoins.

🚀 OPTIMISATIONS:
- Modules C/C++ compilés pour opérations critiques (3-20x plus rapide)
- Librairie mathématique légère en pur Python optimisé
- Fallback automatique si compilation C/C++ indisponible
- Zéro dépendances supplémentaires
"""

import cv2
import numpy as np
from typing import Optional, Dict, List
from pathlib import Path
import sys

from .config import ImageProcessorConfig
from .text_detection import TextDetector, TextRegion
from .shape_detection import ShapeDetector, Shape
from .distance_measurement import DistanceMeasurer, Distance
from .visual_analysis import VisualAnalyzer, VisualAnalysis
from .optimization import ImageOptimizer, FastImageProcessor

# Importation des modules optimisés
from .optimized_adapters import get_optimized_filters, get_optimized_geometry
from . import math_utils

__version__ = "1.0.2"
__author__ = "ImageProcessor Team"

# Les optimisations sont silencieuses par défaut
# Les utilisateurs peuvent vérifier les détails dans le code


class ImageProcessor:
    """
    Gestionnaire central pour le traitement modulaire d'images.
    
    Permet d'utiliser indépendamment chaque module selon les besoins.
    
    Exemple:
        >>> processor = ImageProcessor()
        >>> 
        >>> # Désactiver certains modules
        >>> processor.config.enable_module('text_detection', True)
        >>> processor.config.enable_module('distance_measurement', False)
        >>> 
        >>> # Charger une image
        >>> image = cv2.imread('image.jpg')
        >>> 
        >>> # Utiliser les modules activés
        >>> if processor.config.is_module_enabled('text_detection'):
        >>>     texts = processor.detect_text(image)
        >>> 
        >>> if processor.config.is_module_enabled('shape_detection'):
        >>>     shapes = processor.detect_shapes(image)
    """
    
    def __init__(self, config_file: Optional[str] = None, optimization: str = "balanced"):
        """
        Initialise le processeur d'images.
        
        Args:
            config_file: Chemin optionnel vers un fichier de configuration JSON
            optimization: Profil d'optimisation ("speed", "quality", "balanced")
        """
        self.config = ImageProcessorConfig(config_file)
        self.optimizer = ImageOptimizer(optimization)
        self.optimization_enabled = True
        
        # Initialiser les modules à None - ils seront créés lazily à la demande
        self.text_detector = None
        self.shape_detector = None
        self.distance_measurer = None
        self.visual_analyzer = None
        self._modules_created = {
            'text_detection': False,
            'shape_detection': False,
            'distance_measurement': False,
            'visual_analysis': False
        }
    
    def _ensure_text_detector(self) -> bool:
        """Crée le text_detector si nécessaire et activé. Retourne True si prêt."""
        if not self.config.is_module_enabled('text_detection'):
            return False
        if self._modules_created['text_detection'] and self.text_detector is not None:
            return True
        try:
            options = self.config.get_module_options('text_detection')
            languages = options.get('language', ['en', 'fr'])
            self.text_detector = TextDetector(
                languages=languages,
                engine=options.get('engine', 'easyocr')
            )
            self._modules_created['text_detection'] = True
            return True
        except Exception as e:
            self.text_detector = None
            self._modules_created['text_detection'] = False
            return False
    
    def _ensure_shape_detector(self) -> bool:
        """Crée le shape_detector si nécessaire et activé."""
        if not self.config.is_module_enabled('shape_detection'):
            return False
        if self._modules_created['shape_detection'] and self.shape_detector is not None:
            return True
        try:
            options = self.config.get_module_options('shape_detection')
            self.shape_detector = ShapeDetector(
                min_contour_area=options.get('min_contour_area', 50),
                detect_circles=options.get('detect_circles', True),
                detect_rectangles=options.get('detect_rectangles', True),
                detect_polygons=options.get('detect_polygons', True)
            )
            self._modules_created['shape_detection'] = True
            return True
        except Exception as e:
            self.shape_detector = None
            self._modules_created['shape_detection'] = False
            return False
    
    def _ensure_distance_measurer(self) -> bool:
        """Crée le distance_measurer si nécessaire et activé."""
        if not self.config.is_module_enabled('distance_measurement'):
            return False
        if self._modules_created['distance_measurement'] and self.distance_measurer is not None:
            return True
        try:
            options = self.config.get_module_options('distance_measurement')
            self.distance_measurer = DistanceMeasurer(
                unit=options.get('unit', 'pixels'),
                precision=options.get('precision', 2)
            )
            self._modules_created['distance_measurement'] = True
            return True
        except Exception as e:
            self.distance_measurer = None
            self._modules_created['distance_measurement'] = False
            return False
    
    def _ensure_visual_analyzer(self) -> bool:
        """Crée le visual_analyzer si nécessaire et activé."""
        if not self.config.is_module_enabled('visual_analysis'):
            return False
        if self._modules_created['visual_analysis'] and self.visual_analyzer is not None:
            return True
        try:
            options = self.config.get_module_options('visual_analysis')
            self.visual_analyzer = VisualAnalyzer(
                analyze_brightness=options.get('analyze_brightness', True),
                analyze_contrast=options.get('analyze_contrast', True),
                analyze_hue=options.get('analyze_hue', True),
                bins=options.get('bins', 256)
            )
            self._modules_created['visual_analysis'] = True
            return True
        except Exception as e:
            self.visual_analyzer = None
            self._modules_created['visual_analysis'] = False
            return False
    
    def _init_modules(self) -> None:
        """Initialise les modules selon la configuration. DEPRECATED - utiliser les _ensure_* methods."""
        self._ensure_text_detector()
        self._ensure_shape_detector()
        self._ensure_distance_measurer()
        self._ensure_visual_analyzer()
    
    def detect_text(self, image: np.ndarray, min_confidence: float = 0.5, optimize: bool = True) -> Optional[List[TextRegion]]:
        """
        Détecte le texte dans l'image.
        
        Args:
            image: Image en format numpy array
            min_confidence: Seuil de confiance minimum
            optimize: Appliquer l'optimisation d'image
        
        Returns:
            Liste des régions de texte ou None si module désactivé
        """
        if not self._ensure_text_detector():
            return None
        
        # Optimiser l'image si activé
        if optimize and self.optimization_enabled:
            image, info = self.optimizer.preprocess_image(image)
        
        return self.text_detector.detect(image, min_confidence)
    
    def extract_text(self, image: np.ndarray, min_confidence: float = 0.5, 
                     return_text: bool = True, return_coords: bool = False):
        """
        Extrait le texte d'une image en suivant l'ordre naturel de lecture.
        
        Le développeur peut choisir ce qu'il veut retourner:
        - return_text=True, return_coords=False  → Retourne juste le texte (défaut)
        - return_text=False, return_coords=True  → Retourne juste les coordonnées
        - return_text=True, return_coords=True   → Retourne (texte, coordonnées)
        
        Args:
            image: Image en format numpy array
            min_confidence: Seuil de confiance minimum
            return_text: Si True, retourne le texte
            return_coords: Si True, retourne les coordonnées des régions
        
        Returns:
            - Si return_text=True et return_coords=False:  str (texte extrait)
            - Si return_text=False et return_coords=True:  List[Dict] (coordonnées)
            - Si return_text=True et return_coords=True:   Tuple[str, List[Dict]] (texte, coordonnées)
            - None si module désactivé
        
        Examples:
            # Juste le texte (défaut)
            text = processor.extract_text(image)
            
            # Juste les coordonnées
            coords = processor.extract_text(image, return_text=False, return_coords=True)
            
            # Les deux
            text, coords = processor.extract_text(image, return_coords=True)
        """
        if not self._ensure_text_detector():
            return None
        return self.text_detector.extract_text(image, min_confidence, return_text, return_coords)
    
    def detect_shapes(self, image: np.ndarray, optimize: bool = True) -> Optional[List[Shape]]:
        """
        Détecte les formes géométriques.
        
        Args:
            image: Image en format numpy array
            optimize: Appliquer l'optimisation d'image
        
        Returns:
            Liste des formes détectées ou None si module désactivé
        """
        if not self._ensure_shape_detector():
            return None
        
        # Optimiser l'image si activé
        if optimize and self.optimization_enabled:
            image, info = self.optimizer.preprocess_image(image)
        
        return self.shape_detector.detect_shapes(image)
    
    def detect_circles(self, image: np.ndarray) -> Optional[List[Shape]]:
        """Détecte les cercles."""
        if not self._ensure_shape_detector():
            return None
        return self.shape_detector.detect_circles(image)
    
    def detect_rectangles(self, image: np.ndarray) -> Optional[List[Shape]]:
        """Détecte les rectangles."""
        if not self._ensure_shape_detector():
            return None
        return self.shape_detector.detect_rectangles(image)
    
    def measure_distance(self, point1: tuple, point2: tuple) -> Optional[Distance]:
        """
        Mesure la distance entre deux points.
        
        Args:
            point1: Coordonnées du premier point
            point2: Coordonnées du deuxième point
        
        Returns:
            Objet Distance ou None si module désactivé
        """
        if not self._ensure_distance_measurer():
            return None
        return self.distance_measurer.euclidean_distance(point1, point2)
    
    def analyze_visual_properties(self, image: np.ndarray, optimize: bool = True) -> Optional[VisualAnalysis]:
        """
        Analyse les propriétés visuelles de l'image.
        
        Args:
            image: Image en format numpy array
            optimize: Appliquer l'optimisation d'image
        
        Returns:
            Objet VisualAnalysis ou None si module désactivé
        """
        if not self._ensure_visual_analyzer():
            return None
        
        # Optimiser l'image si activé
        if optimize and self.optimization_enabled:
            image, info = self.optimizer.preprocess_image(image)
        
        return self.visual_analyzer.analyze(image)
    
    def process_image(self, image_path: str) -> Dict:
        """
        Traite une image avec tous les modules activés.
        
        Args:
            image_path: Chemin vers l'image
        
        Returns:
            Dictionnaire avec les résultats de tous les modules
        """
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image non trouvée: {image_path}")
        
        results = {}
        
        # Texte
        if self.config.is_module_enabled('text_detection') and self.text_detector:
            results['text'] = [r.to_dict() for r in self.detect_text(image) or []]
        
        # Formes
        if self.config.is_module_enabled('shape_detection') and self.shape_detector:
            results['shapes'] = [s.to_dict() for s in self.detect_shapes(image) or []]
        
        # Analyse visuelle
        if self.config.is_module_enabled('visual_analysis') and self.visual_analyzer:
            analysis = self.analyze_visual_properties(image)
            if analysis:
                results['visual_analysis'] = analysis.to_dict()
        
        return results
    
    def get_status(self) -> Dict:
        """Retourne le statut de tous les modules."""
        return self.config.get_status()
    
    def __repr__(self) -> str:
        status = {name: config.enabled for name, config in self.config.modules.items()}
        return f"ImageProcessor(modules={status}, optimization={self.optimizer.profile.value})"


__all__ = [
    'ImageProcessor',
    'ImageProcessorConfig',
    'TextDetector',
    'ShapeDetector',
    'DistanceMeasurer',
    'VisualAnalyzer',
    'TextRegion',
    'Shape',
    'Distance',
    'VisualAnalysis',
    'ImageOptimizer',
    'FastImageProcessor'
]
