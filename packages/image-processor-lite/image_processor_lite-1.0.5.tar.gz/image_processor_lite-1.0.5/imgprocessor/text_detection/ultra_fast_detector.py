"""
🔥 ULTRA SPEED MODE - Résolution 10% (96x54)
Objectif: Atteindre < 50ms, idéalement < 1ms
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class TextRegionUltra:
    """Région de texte (ultra-léger)."""
    text: str
    bbox: Tuple[int, int, int, int]

class UltraFastTextDetector:
    """
    Détecteur texte ULTRA-RAPIDE.
    
    ⚡️ Stratégies:
    1. Réduire résolution à 10% (96x54 pixels)
    2. Binarisation agresssive
    3. Contours + OCR tesseract minimal
    4. Cache image
    """
    
    def __init__(self):
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except:
            self.pytesseract = None
    
    def detect_ultra_fast(self, image: np.ndarray) -> str:
        """
        Détecte texte en ultra-rapide (< 50ms).
        
        ⚡️ Stratégie:
        - Réduit à 10% résolution (~96x54px)
        - Binarise agressivement  
        - OCR tesseract avec --psm 6 (bloc de texte)
        """
        if self.pytesseract is None:
            return ""
        
        # 1. Réduire drastiquement (10%)
        h, w = image.shape[:2]
        new_w = max(48, int(w * 0.1))  # min 48px
        new_h = max(24, int(h * 0.1))  # min 24px
        
        small = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 2. Convertir en grayscale + binariser
        if len(small.shape) == 3:
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        else:
            gray = small
        
        # Binarisation agresssive
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # 3. OCR minimal (psm 6 = bloc de texte)
        try:
            config = '--psm 6 --oem 1'  # PSM 6 = bloc de texte, OEM 1 = legacy
            text = self.pytesseract.image_to_string(binary, config=config)
            return text.strip()
        except:
            return ""
    
    def detect_regions(self, image: np.ndarray) -> List[Dict]:
        """Détecte les régions rapidement."""
        if self.pytesseract is None:
            return []
        
        # Même prétraitement que ultra_fast
        h, w = image.shape[:2]
        new_w = max(48, int(w * 0.1))
        new_h = max(24, int(h * 0.1))
        
        small = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        if len(small.shape) == 3:
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        else:
            gray = small
        
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        try:
            # Données détaillées (lent!)
            data = self.pytesseract.image_to_data(binary, output_type=self.pytesseract.Output.DICT)
            
            # Scale back to original
            scale_x = w / new_w if new_w > 0 else 1
            scale_y = h / new_h if new_h > 0 else 1
            
            regions = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and len(text) > 0:
                    regions.append({
                        'text': text,
                        'bbox': (
                            int(data['left'][i] * scale_x),
                            int(data['top'][i] * scale_y),
                            int(data['width'][i] * scale_x),
                            int(data['height'][i] * scale_y)
                        )
                    })
            return regions
        except:
            return []

# Test de performance
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/home/virus-one/Documents/projet/package_dev')
    
    from pathlib import Path
    
    detector = UltraFastTextDetector()
    
    image_path = "/home/virus-one/Documents/projet/amanda1/image.png"
    if Path(image_path).exists():
        img = cv2.imread(image_path)
        
        print("🔥 ULTRA FAST MODE TEST")
        print("=" * 60)
        
        # Test 1
        start = time.perf_counter()
        text = detector.detect_ultra_fast(img)
        t1 = (time.perf_counter() - start) * 1000
        
        print(f"detect_ultra_fast():  {t1:7.2f}ms")
        print(f"Texte extrait ({len(text)} chars):\n  {text[:100]}")
        
        # Test 2
        start = time.perf_counter()
        for _ in range(5):
            detector.detect_ultra_fast(img)
        t2 = (time.perf_counter() - start) * 1000 / 5
        
        print(f"\nMoyenne 5 appels:    {t2:7.2f}ms")
        
        # Test 3 (regions)
        start = time.perf_counter()
        regions = detector.detect_regions(img)
        t3 = (time.perf_counter() - start) * 1000
        
        print(f"detect_regions():    {t3:7.2f}ms")
        print(f"Régions trouvées: {len(regions)}")
