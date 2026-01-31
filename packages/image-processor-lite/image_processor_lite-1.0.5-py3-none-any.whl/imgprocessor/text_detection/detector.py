"""
Module de détection et extraction de texte.
Supporte plusieurs moteurs (EasyOCR, Tesseract).
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
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
        
        # ✅ WARMUP: Pre-warm EasyOCR on init if available
        if engine == 'easyocr':
            try:
                self._warmup_easyocr()
            except:
                pass  # Warmup failure is not critical, will retry on first use
    
    def _warmup_easyocr(self):
        """Pre-warm EasyOCR model with dummy image to reduce first-call latency."""
        if self._is_initialized:
            return
        
        self._lazy_init_easyocr()
        
        if self.reader and self.init_success:
            try:
                # Use tiny dummy image to trigger model loading
                dummy_img = np.zeros((50, 50, 3), dtype=np.uint8)
                _ = self.reader.readtext(dummy_img)
            except:
                pass  # Warmup failure is not critical
        
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
    
    def _sort_regions_by_position(self, regions: List[TextRegion]) -> List[TextRegion]:
        """
        Trie les régions de texte en fonction de leur position dans l'image.
        L'ordre suit la lecture naturelle: de haut en bas, puis de gauche à droite.
        
        Args:
            regions: Liste des régions de texte
        
        Returns:
            Régions triées par position (haut vers bas, gauche vers droite)
        """
        if not regions:
            return regions
        
        # Grouper les régions par ligne (même Y approximativement)
        # On utilise une tolérance pour regrouper les textes au même niveau
        line_height_tolerance = 20  # pixels
        
        lines = []
        sorted_regions = sorted(regions, key=lambda r: r.bbox[1])  # Trier par Y
        
        current_line = []
        current_y = None
        
        for region in sorted_regions:
            y = region.bbox[1]
            
            # Si c'est la première région ou elle est au même niveau que la ligne actuelle
            if current_y is None or abs(y - current_y) <= line_height_tolerance:
                current_line.append(region)
                if current_y is None:
                    current_y = y
            else:
                # Nouvelle ligne détectée
                # Trier la ligne actuelle de gauche à droite
                current_line.sort(key=lambda r: r.bbox[0])
                lines.append(current_line)
                current_line = [region]
                current_y = y
        
        # Ajouter la dernière ligne
        if current_line:
            current_line.sort(key=lambda r: r.bbox[0])
            lines.append(current_line)
        
        # Flatten: fusionner toutes les lignes
        sorted_regions_result = []
        for line in lines:
            sorted_regions_result.extend(line)
        
        return sorted_regions_result
    
    def extract_text(self, image: np.ndarray, min_confidence: float = 0.5, 
                     return_text: bool = True, return_coords: bool = False) -> Union[str, List[Dict], Tuple[str, List[Dict]]]:
        """
        Extrait le texte d'une image en suivant l'ordre naturel de lecture.
        Le texte est ordonné de haut en bas, puis de gauche à droite.
        
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
        
        Raises:
            ValueError: Si return_text et return_coords sont tous les deux False
        
        Examples:
            # Juste le texte (défaut)
            text = detector.extract_text(image)
            
            # Juste les coordonnées
            coords = detector.extract_text(image, return_text=False, return_coords=True)
            
            # Les deux
            text, coords = detector.extract_text(image, return_coords=True)
        """
        if not return_text and not return_coords:
            raise ValueError("Au moins un de return_text ou return_coords doit être True")
        
        regions = self.detect(image, min_confidence)
        if not regions:
            empty_result = ("" if return_text else None, [] if return_coords else None)
            if return_text and return_coords:
                return ("", [])
            elif return_text:
                return ""
            else:
                return []
        
        # Trier les régions par position
        sorted_regions = self._sort_regions_by_position(regions)
        
        # Préparer les résultats selon ce qui est demandé
        result_text = None
        result_coords = None
        
        if return_text:
            result_text = '\n'.join([region.text for region in sorted_regions])
        
        if return_coords:
            result_coords = [region.to_dict() for region in sorted_regions]
        
        # Retourner selon les demandes
        if return_text and return_coords:
            return (result_text, result_coords)
        elif return_text:
            return result_text
        else:
            return result_coords
    
    def get_regions_with_coords(self, image: np.ndarray, min_confidence: float = 0.5) -> List[Dict]:
        """
        Retourne les régions de texte avec leurs coordonnées, triées par position.
        
        Args:
            image: Image en format numpy array
            min_confidence: Seuil de confiance minimum
        
        Returns:
            Régions triées par position (haut vers bas, gauche vers droite)
        """
        regions = self.detect(image, min_confidence)
        sorted_regions = self._sort_regions_by_position(regions)
        return [region.to_dict() for region in sorted_regions]
