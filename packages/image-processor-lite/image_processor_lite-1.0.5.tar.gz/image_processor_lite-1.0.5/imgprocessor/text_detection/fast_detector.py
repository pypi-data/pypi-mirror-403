"""
🔥 ULTRA-FAST TEXT DETECTION MODE
- Tesseract OCR (1000x plus léger que EasyOCR)
- Résolution réduite à 20% (pour texte simple)
- Objectif: < 50ms par détection
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class TextRegionFast:
    """Région de texte détectée (version légère)."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox
        }


class FastTextDetector:
    """
    Détecteur de texte ultra-rapide avec Tesseract.
    
    🚀 PERFORMANCES: ~50-100ms pour images simples
    ✅ Sans dépendances lourdes (EasyOCR, PyTorch)
    """
    
    def __init__(self, mode: str = 'speed'):
        """
        Args:
            mode: 'speed' (ultra-rapide, 20% résolution), 
                  'balanced' (50% résolution), 
                  'quality' (100% résolution)
        """
        self.mode = mode
        self.pytesseract = None
        self._init_tesseract()
        
        # Paramètres de résolution
        self.resize_factor = {
            'speed': 0.2,       # 20% = ultra-rapide!
            'balanced': 0.5,    # 50%
            'quality': 1.0      # 100%
        }.get(mode, 0.5)
    
    def _init_tesseract(self):
        """Initialise Tesseract (léger et rapide)."""
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            raise ImportError("pytesseract required. Install: pip install pytesseract")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Prétraite l'image pour améliorer l'OCR."""
        # Réduire résolution
        h, w = image.shape[:2]
        new_w = int(w * self.resize_factor)
        new_h = int(h * self.resize_factor)
        
        if new_w > 0 and new_h > 0:
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Convertir en grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Binarisation (améliore l'OCR)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        return binary
    
    def detect(self, image: np.ndarray) -> List[TextRegionFast]:
        """Détecte le texte rapidement avec Tesseract."""
        if self.pytesseract is None:
            return []
        
        # Prétraitement
        processed = self._preprocess_image(image)
        
        try:
            # OCR avec Tesseract (très rapide)
            data = self.pytesseract.image_to_data(
                processed, 
                output_type=self.pytesseract.Output.DICT
            )
            
            regions = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and len(text) > 0:
                    conf = float(data['conf'][i]) / 100.0
                    if conf >= 0.3:  # Seuil bas (Tesseract est prudent)
                        regions.append(TextRegionFast(
                            text=text,
                            confidence=conf,
                            bbox=(
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            )
                        ))
            
            return regions
        except Exception as e:
            print(f"OCR Error: {e}")
            return []
    
    def extract_text(self, image: np.ndarray) -> str:
        """Extrait simplement le texte."""
        regions = self.detect(image)
        return '\n'.join([r.text for r in regions]) if regions else ""


__all__ = ['FastTextDetector', 'TextRegionFast']
