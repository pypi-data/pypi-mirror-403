"""
Module d'analyse visuelle des images.
Analyse la luminosité, le contraste, la teinte et autres propriétés visuelles.
Détecte les objets visuels cohérents: régions avec continuité spatiale et stabilité chromatique.
"""

import cv2
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, field
from scipy import ndimage
from hashlib import md5
from . import _native as _native_loader


@dataclass
class VisualObject:
    """Représente un objet visuel détecté."""
    object_id: int
    label: str  # 'unknown', 'natural', 'artificial', 'geometric', 'abstract'
    area: int
    perimeter: float
    centroid: Tuple[float, float]
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    dominant_color: Tuple[int, int, int]  # (B, G, R)
    mean_brightness: float
    chromatic_stability: float  # 0-1, mesure l'homogénéité chromatique
    contour_regularity: float  # 0-1, mesure la régularité du contour
    solidity: float  # 0-1, rapport aire/aire du convex hull
    aspect_ratio: float  # rapport largeur/hauteur


@dataclass
class VisualAnalysis:
    """Résultats de l'analyse visuelle."""
    brightness: float = 0.0
    contrast: float = 0.0
    hue_distribution: Dict = None
    saturation: float = 0.0
    value: float = 0.0
    color_histogram: Dict = None
    edge_density: float = 0.0
    objects: List[VisualObject] = field(default_factory=list)
    object_density: float = 0.0  # nombre d'objets détectés
    
    def __post_init__(self):
        if self.hue_distribution is None:
            self.hue_distribution = {}
        if self.color_histogram is None:
            self.color_histogram = {}
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'brightness': float(self.brightness),
            'contrast': float(self.contrast),
            'hue_distribution': self.hue_distribution,
            'saturation': float(self.saturation),
            'value': float(self.value),
            'color_histogram': self.color_histogram,
            'edge_density': float(self.edge_density),
            'object_count': len(self.objects),
            'object_density': float(self.object_density),
            'objects': [
                {
                    'id': obj.object_id,
                    'label': obj.label,
                    'area': obj.area,
                    'perimeter': float(obj.perimeter),
                    'centroid': obj.centroid,
                    'bounding_box': obj.bounding_box,
                    'dominant_color': obj.dominant_color,
                    'mean_brightness': float(obj.mean_brightness),
                    'chromatic_stability': float(obj.chromatic_stability),
                    'contour_regularity': float(obj.contour_regularity),
                    'solidity': float(obj.solidity),
                    'aspect_ratio': float(obj.aspect_ratio)
                }
                for obj in self.objects
            ]
        }


class VisualAnalyzer:
    """
    Analyste des propriétés visuelles des images.
    Détecte et analyse les objets visuels cohérents.
    """
    
    def __init__(self, 
                 analyze_brightness: bool = True,
                 analyze_contrast: bool = True,
                 analyze_hue: bool = True,
                 detect_objects: bool = True,
                 bins: int = 256,
                 min_object_size: int = 100,
                 max_object_size: Optional[int] = None):
        """
        Initialise l'analyseur visuel.
        
        Args:
            analyze_brightness: Analyser la luminosité
            analyze_contrast: Analyser le contraste
            analyze_hue: Analyser la teinte
            detect_objects: Détecter les objets visuels
            bins: Nombre de bandes pour les histogrammes
            min_object_size: Taille minimale d'objet (pixels)
            max_object_size: Taille maximale d'objet (None = pas de limite)
        """
        self.analyze_brightness = analyze_brightness
        self.analyze_contrast = analyze_contrast
        self.analyze_hue = analyze_hue
        self.detect_objects = detect_objects
        self.bins = bins
        self.min_object_size = min_object_size
        self.max_object_size = max_object_size
        # native acceleration available?
        self._native_available = True
        try:
            # keep loader module; actual functions may raise NotImplementedError
            self._native = _native_loader
        except Exception:
            self._native_available = False
            self._native = None
        
        # ✅ CACHING: Cache results based on image hash
        self._cache = {}
        self._cache_enabled = True
    
    def _get_image_hash(self, image: np.ndarray) -> str:
        """Get MD5 hash of image for caching."""
        try:
            return md5(image.tobytes()).hexdigest()
        except:
            return None
    
    def analyze(self, image: np.ndarray) -> VisualAnalysis:
        """
        Analyse l'image complète.
        
        Args:
            image: Image en format numpy array (BGR)
        
        Returns:
            Objet VisualAnalysis avec tous les résultats
        """
        # ✅ CACHE: Check cache first
        if self._cache_enabled:
            img_hash = self._get_image_hash(image)
            if img_hash and img_hash in self._cache:
                return self._cache[img_hash]
        else:
            img_hash = None
        
        analysis = self._analyze_impl(image)
        
        # ✅ CACHE: Store result
        if self._cache_enabled and img_hash:
            self._cache[img_hash] = analysis
        
        return analysis
    
    def _analyze_impl(self, image: np.ndarray) -> VisualAnalysis:
        """
        Implémentation réelle de l'analyse.
        
        Args:
            image: Image en format numpy array (BGR)
        
        Returns:
            Objet VisualAnalysis avec tous les résultats
        """
        analysis = VisualAnalysis()
        
        # Conversion en niveaux de gris pour luminosité/contraste
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Analyse de la luminosité
        if self.analyze_brightness:
            analysis.brightness = float(np.mean(gray))
        
        # Analyse du contraste
        if self.analyze_contrast:
            analysis.contrast = float(np.std(gray))
        
        # Conversion en HSV pour teinte/saturation/valeur
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Analyse de la teinte
        if self.analyze_hue:
            analysis.hue_distribution = self._analyze_hue(hsv)
            analysis.saturation = float(np.mean(hsv[:, :, 1]))
            analysis.value = float(np.mean(hsv[:, :, 2]))
        
        # Histogramme des couleurs
        analysis.color_histogram = self._compute_color_histogram(image)
        
        # Densité des contours
        analysis.edge_density = self._compute_edge_density(gray)
        
        # Détection des objets visuels cohérents
        if self.detect_objects:
            analysis.objects = self._detect_visual_objects(image, gray, hsv)
            analysis.object_density = len(analysis.objects) / (image.shape[0] * image.shape[1]) * 10000
        
        return analysis
    
    def _analyze_hue(self, hsv_image: np.ndarray) -> Dict:
        """
        Analyse la distribution de la teinte.
        
        Args:
            hsv_image: Image au format HSV
        
        Returns:
            Dictionnaire avec la distribution de teinte
        """
        hue = hsv_image[:, :, 0]
        hist = cv2.calcHist([hsv_image], [0], None, [self.bins], [0, 180])
        hist = hist.flatten()
        hist = hist / hist.sum()  # Normaliser
        
        # Catégoriser les teintes
        hue_categories = {
            'red': float(np.sum(hist[0:15]) + np.sum(hist[165:180])) * 100,
            'orange': float(np.sum(hist[15:30])) * 100,
            'yellow': float(np.sum(hist[30:45])) * 100,
            'green': float(np.sum(hist[45:90])) * 100,
            'cyan': float(np.sum(hist[90:105])) * 100,
            'blue': float(np.sum(hist[105:135])) * 100,
            'magenta': float(np.sum(hist[135:165])) * 100
        }
        
        return hue_categories
    
    def _compute_color_histogram(self, image: np.ndarray) -> Dict:
        """
        Calcule l'histogramme des couleurs.
        
        Args:
            image: Image BGR
        
        Returns:
            Dictionnaire avec les histogrammes B, G, R
        """
        colors = {'blue': 0, 'green': 1, 'red': 2}
        histogram = {}
        
        for color_name, channel_idx in colors.items():
            hist = cv2.calcHist([image], [channel_idx], None, [self.bins], [0, 256])
            hist = hist.flatten()
            # Retourner les 10 valeurs les plus importantes
            top_indices = np.argsort(hist)[-10:][::-1]
            histogram[color_name] = {
                'mean': float(np.mean(image[:, :, channel_idx])),
                'std': float(np.std(image[:, :, channel_idx])),
                'top_bins': [int(i) for i in top_indices]
            }
        
        return histogram
    
    def _compute_edge_density(self, gray_image: np.ndarray) -> float:
        """
        Calcule la densité des contours (edges).
        
        Args:
            gray_image: Image en niveaux de gris
        
        Returns:
            Densité des contours (0-100)
        """
        edges = cv2.Canny(gray_image, 100, 200)
        edge_count = np.count_nonzero(edges)
        total_pixels = gray_image.shape[0] * gray_image.shape[1]
        edge_density = (edge_count / total_pixels) * 100
        
        return float(edge_density)
    
    def get_brightness_level(self, image: np.ndarray) -> str:
        """
        Retourne le niveau de luminosité.
        
        Args:
            image: Image
        
        Returns:
            'very_dark', 'dark', 'normal', 'bright', 'very_bright'
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        if brightness < 50:
            return 'very_dark'
        elif brightness < 100:
            return 'dark'
        elif brightness < 150:
            return 'normal'
        elif brightness < 200:
            return 'bright'
        else:
            return 'very_bright'
    
    def get_contrast_level(self, image: np.ndarray) -> str:
        """
        Retourne le niveau de contraste.
        
        Args:
            image: Image
        
        Returns:
            'low', 'medium', 'high', 'very_high'
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        
        if contrast < 30:
            return 'low'
        elif contrast < 60:
            return 'medium'
        elif contrast < 100:
            return 'high'
        else:
            return 'very_high'
    
    def get_dominant_color(self, image: np.ndarray) -> Tuple[int, int, int]:
        """
        Retourne la couleur dominante.
        
        Args:
            image: Image
        
        Returns:
            Tuple (B, G, R) de la couleur dominante
        """
        # Redimensionner pour accélération
        img_small = cv2.resize(image, (150, 150))
        img_flat = img_small.reshape((-1, 3))
        img_float = np.float32(img_flat)
        
        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, _, centers = cv2.kmeans(img_float, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        dominant_color = tuple(map(int, centers[0]))
        return dominant_color
    
    def compare_images(self, image1: np.ndarray, image2: np.ndarray) -> Dict:
        """
        Compare deux images.
        
        Args:
            image1: Première image
            image2: Deuxième image
        
        Returns:
            Dictionnaire avec les différences
        """
        analysis1 = self.analyze(image1)
        analysis2 = self.analyze(image2)
        
        comparison = {
            'brightness_diff': abs(analysis1.brightness - analysis2.brightness),
            'contrast_diff': abs(analysis1.contrast - analysis2.contrast),
            'saturation_diff': abs(analysis1.saturation - analysis2.saturation),
            'edge_density_diff': abs(analysis1.edge_density - analysis2.edge_density),
            'image1_brightness_level': self.get_brightness_level(image1),
            'image2_brightness_level': self.get_brightness_level(image2),
            'image1_contrast_level': self.get_contrast_level(image1),
            'image2_contrast_level': self.get_contrast_level(image2)
        }
        
        return comparison
    
    def enhance_image(self, image: np.ndarray, 
                     brightness_factor: float = 1.0,
                     contrast_factor: float = 1.0) -> np.ndarray:
        """
        Améliore une image.
        
        Args:
            image: Image
            brightness_factor: Facteur de luminosité (1.0 = pas de changement)
            contrast_factor: Facteur de contraste (1.0 = pas de changement)
        
        Returns:
            Image améliorée
        """
        # Appliquer le contraste
        enhanced = cv2.convertScaleAbs(image, alpha=contrast_factor, beta=0)
        
        # Appliquer la luminosité
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.0, beta=(brightness_factor - 1.0) * 255)
        
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    
    # ============= DÉTECTION D'OBJETS VISUELS COHÉRENTS =============
    
    def _detect_visual_objects(self, image: np.ndarray, gray: np.ndarray, 
                               hsv: np.ndarray) -> List[VisualObject]:
        """
        Détecte les régions visuelles cohérentes (objets).
        Utilise une combinaison de:
        - segmentation par couleur (stabilité chromatique)
        - analyse de contours (frontières mesurables)
        - continuité spatiale (connected components)
        
        Args:
            image: Image originale BGR
            gray: Image en niveaux de gris
            hsv: Image en HSV
        
        Returns:
            Liste des objets détectés
        """
        objects = []
        
        # Étape 1: Créer une segmentation par couleur (K-means)
        color_mask = self._segment_by_color(image)
        
        # Étape 2: Améliorer la segmentation avec une morphologie
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
        
        # Étape 3: Détecter les contours
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Étape 4: Analyser chaque contour
        object_id = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filtrer par taille
            if area < self.min_object_size:
                continue
            if self.max_object_size and area > self.max_object_size:
                continue
            
            # Créer un objet VisualObject
            visual_obj = self._analyze_contour(image, gray, hsv, contour, 
                                              object_id, color_mask)
            if visual_obj:
                objects.append(visual_obj)
                object_id += 1
        
        return objects
    
    def _segment_by_color(self, image: np.ndarray, k: int = 5) -> np.ndarray:
        """
        Segmente l'image en régions homogènes par couleur (K-means).
        Crée un masque binaire des régions principales.
        
        Args:
            image: Image BGR
            k: Nombre de clusters de couleur
        
        Returns:
            Masque binaire des régions
        """
        # Try native implementation first (if compiled)
        if self._native is not None:
            try:
                res = self._native.segment_by_color(image, k)
                # Validate native result
                if isinstance(res, np.ndarray):
                    return res
            except NotImplementedError:
                pass
            except Exception:
                # Any error from native: fallback to Python
                pass

        # Fallback Python implementation
        h, w = image.shape[:2]
        img_small = cv2.resize(image, (min(w, 300), min(h, 300)))

        data = img_small.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        cluster_sizes = np.bincount(labels.flatten())
        main_clusters = np.argsort(cluster_sizes)[-2:]

        mask = np.zeros(labels.shape, dtype=np.uint8)
        for cluster_id in main_clusters:
            mask[labels == cluster_id] = 255

        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        return mask
    
    def _analyze_contour(self, image: np.ndarray, gray: np.ndarray, 
                        hsv: np.ndarray, contour: np.ndarray, 
                        obj_id: int, mask: np.ndarray) -> Optional[VisualObject]:
        """
        Analyse un contour donné et crée un objet VisualObject.
        
        Args:
            image: Image originale BGR
            gray: Image en niveaux de gris
            hsv: Image en HSV
            contour: Contour OpenCV
            obj_id: ID de l'objet
            mask: Masque de segmentation
        
        Returns:
            VisualObject ou None si invalide
        """
        # Propriétés géométriques
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return None
        
        # Centroid
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return None
        centroid = (M["m10"] / M["m00"], M["m01"] / M["m00"])
        
        # Bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Solidity (rapport aire/convex hull)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Aspect ratio
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Contour regularity (compacité)
        contour_regularity = (4 * np.pi * area) / (perimeter ** 2)
        
        # Extraire la région pour analyse de couleur
        region_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(region_mask, [contour], 0, 255, -1)
        
        # Chromatic stability (homogénéité chromatique)
        chromatic_stability = self._compute_chromatic_stability(
            image, hsv, region_mask
        )
        
        # Couleur dominante dans la région
        dominant_color = self._get_region_dominant_color(image, region_mask)
        
        # Luminosité moyenne dans la région
        mean_brightness = float(np.mean(gray[region_mask == 255]))
        
        # Classification du type d'objet
        label = self._classify_object(
            chromatic_stability, contour_regularity, aspect_ratio, area
        )
        
        return VisualObject(
            object_id=obj_id,
            label=label,
            area=int(area),
            perimeter=float(perimeter),
            centroid=centroid,
            bounding_box=(x, y, w, h),
            dominant_color=dominant_color,
            mean_brightness=mean_brightness,
            chromatic_stability=chromatic_stability,
            contour_regularity=min(contour_regularity, 1.0),
            solidity=float(solidity),
            aspect_ratio=aspect_ratio
        )
    
    def _compute_chromatic_stability(self, image: np.ndarray, 
                                    hsv: np.ndarray, mask: np.ndarray) -> float:
        """
        Mesure l'homogénéité chromatique d'une région.
        Plus la valeur est proche de 1, plus la région est chromatiquement stable.
        
        Args:
            image: Image BGR
            hsv: Image HSV
            mask: Masque de la région
        
        Returns:
            Score de stabilité chromatique (0-1)
        """
        # Try native implementation first
        if self._native is not None:
            try:
                val = self._native.compute_chromatic_stability(hsv, mask)
                # Validate numeric return
                if isinstance(val, (float, int)):
                    return float(val)
            except NotImplementedError:
                pass
            except Exception:
                pass

        # Fallback Python implementation
        s_channel = hsv[:, :, 1]
        region_saturation = s_channel[mask == 255]

        if len(region_saturation) == 0:
            return 0.0

        mean_sat = np.mean(region_saturation)
        std_sat = np.std(region_saturation)

        sat_score = min(mean_sat / 255, 1.0)
        var_score = 1.0 - (std_sat / 255)

        stability = (sat_score + var_score) / 2
        return float(max(0, min(stability, 1.0)))
    
    def _get_region_dominant_color(self, image: np.ndarray, 
                                  mask: np.ndarray) -> Tuple[int, int, int]:
        """
        Extrait la couleur dominante d'une région.
        
        Args:
            image: Image BGR
            mask: Masque de la région
        
        Returns:
            Tuple (B, G, R)
        """
        region = image[mask == 255]
        if len(region) == 0:
            return (0, 0, 0)
        
        # Moyenne des couleurs dans la région
        dominant = tuple(np.mean(region, axis=0).astype(int))
        return dominant
    
    def _classify_object(self, chromatic_stability: float, 
                        contour_regularity: float, aspect_ratio: float,
                        area: int) -> str:
        """
        Classifie un objet détecté.
        
        Categories:
        - 'geometric': Formes régulières, homogènes
        - 'artificial': Contours nets, chromatique stable
        - 'natural': Chromatique stable, irrégulier
        - 'abstract': Zones de couleur sans forme claire
        - 'unknown': Défaut de classification
        
        Args:
            chromatic_stability: Homogénéité chromatique (0-1)
            contour_regularity: Régularité du contour (0-1)
            aspect_ratio: Ratio largeur/hauteur
            area: Surface de l'objet
        
        Returns:
            Label de classification
        """
        # Objets géométriques: très réguliers, très homogènes
        if contour_regularity > 0.7 and chromatic_stability > 0.6:
            # Aspect ratio proches de 1 = carré/cercle
            if 0.5 < aspect_ratio < 2.0:
                return 'geometric'
        
        # Objets artificiels: contours nets, chromatique stable
        if contour_regularity > 0.5 and chromatic_stability > 0.5:
            return 'artificial'
        
        # Objets naturels: chromatique stable mais irréguliers
        if chromatic_stability > 0.4:
            return 'natural'
        
        # Objets abstraits: faible stabilité chromatique
        if area > 100:
            return 'abstract'
        
        return 'unknown'

    def draw_bounding_boxes(self, image: np.ndarray, analysis: VisualAnalysis,
                            color: Tuple[int, int, int] = (0, 255, 0),
                            thickness: int = 2,
                            font_scale: float = 0.5,
                            show_labels: bool = True) -> np.ndarray:
        """
        Dessine des encadrements autour des objets détectés retournés dans
        `analysis.objects`.

        Args:
            image: Image BGR (sera copiée avant modification)
            analysis: Résultats de `analyze()` contenant `objects`
            color: Couleur du rectangle (B, G, R)
            thickness: Épaisseur des lignes
            font_scale: Taille du texte pour les labels
            show_labels: Si True, affiche `id:label` au-dessus de chaque box

        Returns:
            Image annotée (nouveau numpy.ndarray)
        """
        annotated = image.copy()

        for obj in analysis.objects:
            x, y, w, h = obj.bounding_box
            # dessiner le rectangle
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)

            if show_labels:
                label = f"{obj.object_id}:{obj.label}"
                # calculer position du texte
                text_pos = (x, y - 6 if y - 6 > 6 else y + 12)
                # arrière-plan pour lisibilité
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
                cv2.rectangle(annotated, (text_pos[0], text_pos[1] - th - 2),
                              (text_pos[0] + tw, text_pos[1] + 2), color, -1)
                cv2.putText(annotated, label, (text_pos[0], text_pos[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

        return annotated

