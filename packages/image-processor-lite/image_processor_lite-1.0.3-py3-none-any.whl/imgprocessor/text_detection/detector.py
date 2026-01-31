"""
Module de détection et extraction de texte.
Supporte plusieurs moteurs (EasyOCR, Tesseract).
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TextRegion:
    """Représente une région de texte détectée."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    language: str
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox,
            'language': self.language
        }


class TextDetector:
    """
    Détecteur de texte utilisant EasyOCR ou Tesseract.
    ✅ VERSION OPTIMISÉE: Lazy-loading du moteur OCR (chargement à la demande)
    """
    
    def __init__(self, languages: List[str] = None, engine: str = 'easyocr'):
        """
        Initialise le détecteur de texte.
        
        ✅ OPTIMISATION: Le moteur OCR n'est chargé que lors du premier usage
        
        Args:
            languages: Liste des langues à reconnaître (ex: ['en', 'fr'])
            engine: Moteur OCR à utiliser ('easyocr' ou 'tesseract')
        """
        # Normaliser les codes de langue pour easyOCR (en lieu de eng, fr lieu de fra)
        if languages is None:
            languages = ['en', 'fr']
        else:
            # Convertir fra->fr, eng->en pour compatibilité easyOCR
            normalized = []
            lang_map = {'fra': 'fr', 'eng': 'en', 'fre': 'fr', 'english': 'en', 'french': 'fr'}
            for lang in languages:
                normalized.append(lang_map.get(lang.lower(), lang))
            languages = normalized
        
        self.languages = languages
        self.engine = engine
        
        # ✅ LAZY LOADING: Ne pas charger le moteur à l'initialisation
        self.reader = None
        self.pytesseract = None
        self.init_success = False
        self._is_initialized = False  # Flag pour lazy-loading
        
    def _lazy_init_easyocr(self):
        """Initialise EasyOCR à la demande (lazy-loading)."""
        if self._is_initialized or self.engine != 'easyocr':
            return
        
        try:
            import easyocr
            # Essayer avec les langues spécifiées, fallback sur 'en' si erreur
            try:
                self.reader = easyocr.Reader(self.languages, gpu=False, verbose=False)
                self.init_success = True
            except Exception as lang_error:
                # Fallback silencieux sur anglais
                try:
                    self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                    self.init_success = True
                    self.languages = ['en']
                except Exception as fallback_error:
                    # easyOCR non disponible, fallback silencieux
                    pass
        except ImportError:
            raise ImportError("easyocr non installé. Installez avec: pip install easyocr")
        
        self._is_initialized = True
    
    def _lazy_init_tesseract(self):
        """Initialise Tesseract à la demande (lazy-loading)."""
        if self._is_initialized or self.engine != 'tesseract':
            return
        
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.init_success = True
        except ImportError:
            raise ImportError("pytesseract non installé. Installez avec: pip install pytesseract")
        
        self._is_initialized = True
    
    def detect(self, image: np.ndarray, min_confidence: float = 0.5) -> List[TextRegion]:
        """
        Détecte le texte dans une image.
        
        ✅ OPTIMISATION: Initialise le moteur OCR à la première utilisation seulement
        
        Args:
            image: Image en format numpy array (BGR ou RGB)
            min_confidence: Seuil de confiance minimum
        
        Returns:
            Liste des régions de texte détectées
        """
        # ✅ LAZY LOADING: Initialiser le moteur seulement au premier usage
        if self.engine == 'easyocr':
            self._lazy_init_easyocr()
        elif self.engine == 'tesseract':
            self._lazy_init_tesseract()
        
        if not self.init_success:
            # Moteur OCR non initialisé correctement
            return []
        
        if self.engine == 'easyocr':
            return self._detect_easyocr(image, min_confidence)
        elif self.engine == 'tesseract':
            return self._detect_tesseract(image, min_confidence)
        return []
    
    def _detect_easyocr(self, image: np.ndarray, min_confidence: float) -> List[TextRegion]:
        """Détection avec EasyOCR avec prétraitement amélioré."""
        if self.reader is None:
            return []
        
        # Prétraitement pour améliorer la détection
        # Conversion en RGB (easyOCR préfère RGB)
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        try:
            results = self.reader.readtext(rgb_image, detail=1)
        except Exception as e:
            # Erreur easyOCR, retour vide silencieux
            return []
        
        text_regions = []
        for detection in results:
            bbox_points = detection[0]
            text = detection[1]
            confidence = detection[2]
            
            if confidence >= min_confidence:
                # Convertir les points du bbox en coordonnées (x, y, w, h)
                x_coords = [p[0] for p in bbox_points]
                y_coords = [p[1] for p in bbox_points]
                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - x)
                h = int(max(y_coords) - y)
                
                region = TextRegion(
                    text=text,
                    confidence=float(confidence),
                    bbox=(x, y, w, h),
                    language='mixed'
                )
                text_regions.append(region)
        
        return text_regions
    
    def _detect_tesseract(self, image: np.ndarray, min_confidence: float) -> List[TextRegion]:
        """Détection avec Tesseract."""
        # Prétraitement optionnel
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        data = self.pytesseract.image_to_data(gray, output_type=self.pytesseract.Output.DICT)
        
        text_regions = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = float(data['conf'][i]) / 100.0
            
            if text and confidence >= min_confidence:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                region = TextRegion(
                    text=text,
                    confidence=confidence,
                    bbox=(x, y, w, h),
                    language='unknown'
                )
                text_regions.append(region)
        
        return text_regions
    
    def extract_text(self, image: np.ndarray, min_confidence: float = 0.5) -> str:
        """
        Extrait tout le texte d'une image.
        
        Args:
            image: Image en format numpy array
            min_confidence: Seuil de confiance minimum
        
        Returns:
            Chaîne contenant tout le texte détecté
        """
        regions = self.detect(image, min_confidence)
        return '\n'.join([region.text for region in regions])
    
    def get_regions_with_coords(self, image: np.ndarray, min_confidence: float = 0.5) -> List[Dict]:
        """Retourne les régions de texte avec leurs coordonnées."""
        regions = self.detect(image, min_confidence)
        return [region.to_dict() for region in regions]
