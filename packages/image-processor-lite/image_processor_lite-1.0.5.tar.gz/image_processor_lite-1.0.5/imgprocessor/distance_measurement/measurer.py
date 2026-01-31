"""
Module de mesure de distances entre objets.
Permet de calculer les distances entre contours et points détectés.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class Distance:
    """Représente une mesure de distance."""
    distance: float
    unit: str
    from_point: Tuple[float, float]
    to_point: Tuple[float, float]
    object1_id: Optional[int] = None
    object2_id: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'distance': float(self.distance),
            'unit': self.unit,
            'from_point': self.from_point,
            'to_point': self.to_point,
            'object1_id': self.object1_id,
            'object2_id': self.object2_id
        }


class DistanceMeasurer:
    """
    Calcule les distances entre objets dans une image.
    Supporte plusieurs unités (pixels, mm, cm).
    """
    
    def __init__(self, unit: str = 'pixels', precision: int = 2, pixels_per_mm: float = 1.0):
        """
        Initialise le mesureur de distance.
        
        Args:
            unit: Unité de mesure ('pixels', 'mm', 'cm')
            precision: Nombre de décimales
            pixels_per_mm: Conversion pixels -> mm (calibration)
        """
        self.unit = unit
        self.precision = precision
        self.pixels_per_mm = pixels_per_mm
    
    def _convert_distance(self, pixels: float) -> float:
        """Convertit une distance en pixels vers l'unité définie."""
        if self.unit == 'pixels':
            return pixels
        elif self.unit == 'mm':
            return pixels / self.pixels_per_mm
        elif self.unit == 'cm':
            return pixels / (self.pixels_per_mm * 10)
        else:
            raise ValueError(f"Unité inconnue: {self.unit}")
    
    def euclidean_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> Distance:
        """
        Calcule la distance euclidienne entre deux points.
        
        Args:
            point1: Coordonnées du premier point (x, y)
            point2: Coordonnées du deuxième point (x, y)
        
        Returns:
            Objet Distance
        """
        dist_pixels = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
        dist_converted = self._convert_distance(dist_pixels)
        dist_rounded = round(dist_converted, self.precision)
        
        return Distance(
            distance=dist_rounded,
            unit=self.unit,
            from_point=point1,
            to_point=point2
        )
    
    def contour_to_contour_distance(self, contour1: np.ndarray, 
                                   contour2: np.ndarray) -> Distance:
        """
        Calcule la distance minimale entre deux contours.
        
        Args:
            contour1: Premier contour
            contour2: Deuxième contour
        
        Returns:
            Objet Distance
        """
        min_dist = float('inf')
        closest_points = None
        
        for point1 in contour1:
            for point2 in contour2:
                p1 = tuple(point1[0])
                p2 = tuple(point2[0])
                dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                
                if dist < min_dist:
                    min_dist = dist
                    closest_points = (p1, p2)
        
        dist_converted = self._convert_distance(min_dist)
        dist_rounded = round(dist_converted, self.precision)
        
        return Distance(
            distance=dist_rounded,
            unit=self.unit,
            from_point=closest_points[0],
            to_point=closest_points[1]
        )
    
    def point_to_contour_distance(self, point: Tuple[float, float], 
                                 contour: np.ndarray) -> Distance:
        """
        Calcule la distance minimale entre un point et un contour.
        
        Args:
            point: Coordonnées du point (x, y)
            contour: Contour
        
        Returns:
            Objet Distance
        """
        dist = cv2.pointPolygonTest(contour, point, True)
        dist_pixels = abs(dist)
        dist_converted = self._convert_distance(dist_pixels)
        dist_rounded = round(dist_converted, self.precision)
        
        # Trouver le point le plus proche sur le contour
        closest_point = None
        min_dist = float('inf')
        for cont_point in contour:
            p = tuple(cont_point[0])
            d = np.sqrt((p[0] - point[0])**2 + (p[1] - point[1])**2)
            if d < min_dist:
                min_dist = d
                closest_point = p
        
        return Distance(
            distance=dist_rounded,
            unit=self.unit,
            from_point=point,
            to_point=closest_point or point
        )
    
    def distances_between_contours(self, contours: List[np.ndarray]) -> List[Distance]:
        """
        Calcule les distances entre tous les contours.
        
        Args:
            contours: Liste des contours
        
        Returns:
            Liste des distances entre tous les paires
        """
        distances = []
        
        for i in range(len(contours)):
            for j in range(i + 1, len(contours)):
                dist = self.contour_to_contour_distance(contours[i], contours[j])
                dist.object1_id = i
                dist.object2_id = j
                distances.append(dist)
        
        return distances
    
    def set_calibration(self, pixels_per_mm: float) -> None:
        """
        Défini l'étalonnage en pixels par millimètre.
        
        Args:
            pixels_per_mm: Nombre de pixels correspondant à 1mm
        """
        self.pixels_per_mm = pixels_per_mm
    
    def measure_line_distance(self, image: np.ndarray, 
                             point1: Tuple[int, int], 
                             point2: Tuple[int, int]) -> Distance:
        """
        Mesure la distance entre deux points sur une image.
        
        Args:
            image: Image (non utilisée mais pour cohérence)
            point1: Premier point
            point2: Deuxième point
        
        Returns:
            Objet Distance
        """
        return self.euclidean_distance(point1, point2)
    
    def draw_distance_line(self, image: np.ndarray, 
                          distance: Distance, 
                          color: Tuple = (0, 255, 0),
                          thickness: int = 2) -> np.ndarray:
        """
        Dessine une ligne de distance sur l'image.
        
        Args:
            image: Image originale
            distance: Objet Distance à dessiner
            color: Couleur (B, G, R)
            thickness: Épaisseur de la ligne
        
        Returns:
            Image avec la ligne dessinée
        """
        result = image.copy()
        
        p1 = tuple(map(int, distance.from_point))
        p2 = tuple(map(int, distance.to_point))
        
        # Dessiner la ligne
        cv2.line(result, p1, p2, color, thickness)
        
        # Dessiner les points
        cv2.circle(result, p1, 5, color, -1)
        cv2.circle(result, p2, 5, color, -1)
        
        # Afficher la distance
        mid_point = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        text = f"{distance.distance}{distance.unit}"
        cv2.putText(result, text, mid_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return result
