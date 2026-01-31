"""
Module de détection de formes géométriques.
Détecte les cercles, rectangles, polygones et autres contours.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Shape:
    """Représente une forme détectée."""
    shape_type: str  # 'circle', 'rectangle', 'polygon', 'contour'
    center: Tuple[float, float]
    area: float
    perimeter: float
    contour: np.ndarray  # Points du contour
    properties: Dict  # Propriétés spécifiques à la forme
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'shape_type': self.shape_type,
            'center': self.center,
            'area': float(self.area),
            'perimeter': float(self.perimeter),
            'properties': self.properties
        }


class ShapeDetector:
    """
    Détecteur de formes géométriques dans les images.
    """
    
    def __init__(self, 
                 min_contour_area: int = 50,
                 detect_circles: bool = True,
                 detect_rectangles: bool = True,
                 detect_polygons: bool = True):
        """
        Initialise le détecteur de formes.
        
        Args:
            min_contour_area: Surface minimale pour un contour (défaut: 50)
            detect_circles: Activer détection de cercles
            detect_rectangles: Activer détection de rectangles
            detect_polygons: Activer détection de polygones
        
        ✅ OPTIMISATION: min_contour_area filter réduit les contours à traiter
        """
        self.min_contour_area = min_contour_area
        self.enable_circles = detect_circles
        self.enable_rectangles = detect_rectangles
        self.enable_polygons = detect_polygons
    
    def detect_contours(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Détecte tous les contours dans l'image.
        
        Args:
            image: Image en format numpy array
        
        Returns:
            Liste des contours détectés
        """
        # Conversion en niveaux de gris
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Application d'un filtre gaussien
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Détection de contours
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer par surface minimale
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= self.min_contour_area]
        
        return filtered_contours
    
    def detect_circles(self, image: np.ndarray, 
                      dp: float = 1.0,
                      min_dist: int = 50,
                      param1: int = 100,
                      param2: int = 30,
                      min_radius: int = 10,
                      max_radius: int = 100) -> List[Dict]:
        """
        Détecte les cercles dans l'image.
        
        Args:
            image: Image en format numpy array
            dp: Rapport inverse de l'accumulation
            min_dist: Distance minimale entre les centres
            param1, param2: Paramètres de Canny et seuil
            min_radius, max_radius: Rayons min/max
        
        Returns:
            Liste des cercles détectés
        """
        if not self.enable_circles:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        
        detected_circles = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            for circle in circles[0, :]:
                x, y, radius = circle
                area = np.pi * radius ** 2
                perimeter = 2 * np.pi * radius
                
                shape = Shape(
                    shape_type='circle',
                    center=(float(x), float(y)),
                    area=float(area),
                    perimeter=float(perimeter),
                    contour=np.array([]),
                    properties={
                        'radius': int(radius),
                        'diameter': int(2 * radius)
                    }
                )
                detected_circles.append(shape)
        
        return detected_circles
    
    def detect_rectangles(self, image: np.ndarray) -> List[Shape]:
        """Détecte les rectangles dans l'image."""
        if not self.enable_rectangles:
            return []
        
        contours = self.detect_contours(image)
        rectangles = []
        
        for contour in contours:
            # Approximer le contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Vérifier si c'est un rectangle (4 côtés)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # Calculer le centre
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0
                
                # Obtenir le rectangle englobant
                x, y, w, h = cv2.boundingRect(contour)
                
                shape = Shape(
                    shape_type='rectangle',
                    center=(cx, cy),
                    area=float(area),
                    perimeter=float(perimeter),
                    contour=contour,
                    properties={
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h
                    }
                )
                rectangles.append(shape)
        
        return rectangles
    
    def detect_shapes(self, image: np.ndarray) -> List[Shape]:
        """
        Détecte tous les types de formes dans l'image.
        
        Args:
            image: Image en format numpy array
        
        Returns:
            Liste de toutes les formes détectées
        """
        shapes = []
        
        # Détecter les cercles
        if self.enable_circles:
            shapes.extend(self.detect_circles(image))
        
        # Détecter les rectangles
        if self.enable_rectangles:
            shapes.extend(self.detect_rectangles(image))
        
        # Détecter les autres polygones
        if self.enable_polygons:
            shapes.extend(self._detect_polygons(image))
        
        return shapes
    
    def _detect_polygons(self, image: np.ndarray) -> List[Shape]:
        """Détecte les polygones (non rectangles, non cercles)."""
        contours = self.detect_contours(image)
        polygons = []
        
        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Ignorer les rectangles et les formes fermées
            if len(approx) > 4:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0
                
                shape = Shape(
                    shape_type='polygon',
                    center=(cx, cy),
                    area=float(area),
                    perimeter=float(perimeter),
                    contour=contour,
                    properties={
                        'sides': len(approx),
                        'vertices': [(int(p[0][0]), int(p[0][1])) for p in approx]
                    }
                )
                polygons.append(shape)
        
        return polygons
    
    def draw_shapes(self, image: np.ndarray, shapes: List[Shape], color: Tuple = (0, 255, 0)) -> np.ndarray:
        """
        Dessine les formes détectées sur l'image.
        
        Args:
            image: Image originale
            shapes: Liste des formes à dessiner
            color: Couleur (B, G, R)
        
        Returns:
            Image avec les formes dessinées
        """
        result = image.copy()
        
        for shape in shapes:
            if shape.shape_type == 'circle':
                radius = shape.properties.get('radius', 10)
                center = tuple(map(int, shape.center))
                cv2.circle(result, center, radius, color, 2)
            
            elif shape.shape_type in ['rectangle', 'polygon']:
                if len(shape.contour) > 0:
                    cv2.drawContours(result, [shape.contour], 0, color, 2)
        
        return result
