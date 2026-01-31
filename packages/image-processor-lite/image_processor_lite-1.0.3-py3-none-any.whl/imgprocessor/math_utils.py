"""
Librairie mathématique optimisée en pur Python.
Remplace partiellement NumPy pour les opérations essentielles.
Permet de réduire les dépendances externes.
"""

import math
from typing import List, Tuple, Optional, Union


class Vector:
    """Vecteur 2D optimisé."""
    
    __slots__ = ('x', 'y')
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector':
        return Vector(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector':
        return Vector(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector':
        return Vector(self.x / scalar, self.y / scalar)
    
    def dot(self, other: 'Vector') -> float:
        """Produit scalaire."""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector') -> float:
        """Produit vectoriel 2D (retourne un scalaire)."""
        return self.x * other.y - self.y * other.x
    
    def magnitude(self) -> float:
        """Norme euclidienne."""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def magnitude_squared(self) -> float:
        """Norme au carré (plus rapide, pas de sqrt)."""
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> 'Vector':
        """Vecteur unitaire."""
        mag = self.magnitude()
        if mag == 0:
            return Vector(0, 0)
        return Vector(self.x / mag, self.y / mag)
    
    def distance_to(self, other: 'Vector') -> float:
        """Distance euclidienne à un autre vecteur."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def distance_to_squared(self, other: 'Vector') -> float:
        """Distance au carré."""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy
    
    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"


class Matrix2x2:
    """Matrice 2x2 pour transformations 2D."""
    
    def __init__(self, a: float, b: float, c: float, d: float):
        self.a, self.b = a, b
        self.c, self.d = c, d
    
    def __mul__(self, other: Union['Matrix2x2', Vector]) -> Union['Matrix2x2', Vector]:
        if isinstance(other, Matrix2x2):
            return Matrix2x2(
                self.a * other.a + self.b * other.c,
                self.a * other.b + self.b * other.d,
                self.c * other.a + self.d * other.c,
                self.c * other.b + self.d * other.d
            )
        elif isinstance(other, Vector):
            return Vector(
                self.a * other.x + self.b * other.y,
                self.c * other.x + self.d * other.y
            )
    
    def determinant(self) -> float:
        """Déterminant de la matrice."""
        return self.a * self.d - self.b * self.c
    
    def inverse(self) -> 'Matrix2x2':
        """Inverse de la matrice."""
        det = self.determinant()
        if det == 0:
            raise ValueError("Matrice singulière")
        return Matrix2x2(
            self.d / det, -self.b / det,
            -self.c / det, self.a / det
        )
    
    @staticmethod
    def rotation(angle: float) -> 'Matrix2x2':
        """Matrice de rotation (angle en radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix2x2(cos_a, -sin_a, sin_a, cos_a)
    
    @staticmethod
    def scale(sx: float, sy: float) -> 'Matrix2x2':
        """Matrice d'échelle."""
        return Matrix2x2(sx, 0, 0, sy)


class FastMath:
    """Opérations mathématiques critiques optimisées."""
    
    @staticmethod
    def fast_sqrt(x: float) -> float:
        """Racine carrée rapide (approximation Newton-Raphson)."""
        if x < 0:
            return 0
        if x == 0:
            return 0
        
        # Première approximation
        y = x
        # Une itération suffit généralement
        y = (y + x / y) * 0.5
        return y
    
    @staticmethod
    def fast_inverse_sqrt(x: float) -> float:
        """Inverse racine carrée (1/sqrt(x)) ultra-rapide."""
        if x <= 0:
            return float('inf')
        
        # Approximation rapide
        y = x
        y = (3.0 - x * y * y) * y * 0.5
        return y
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Restreint une valeur à un intervalle."""
        return max(min_val, min(max_val, value))
    
    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        """Interpolation linéaire."""
        return a + (b - a) * t
    
    @staticmethod
    def smooth_step(t: float) -> float:
        """Interpolation lissée (Hermite)."""
        t = FastMath.clamp(t, 0, 1)
        return t * t * (3 - 2 * t)
    
    @staticmethod
    def degrees_to_radians(degrees: float) -> float:
        """Conversion degrés -> radians."""
        return degrees * math.pi / 180.0
    
    @staticmethod
    def radians_to_degrees(radians: float) -> float:
        """Conversion radians -> degrés."""
        return radians * 180.0 / math.pi
    
    @staticmethod
    def angle_between(v1: Vector, v2: Vector) -> float:
        """Angle entre deux vecteurs (en radians)."""
        dot = v1.dot(v2)
        det = v1.cross(v2)
        return math.atan2(det, dot)
    
    @staticmethod
    def point_on_line(point: Vector, line_start: Vector, 
                     line_end: Vector) -> float:
        """Projection paramétrique d'un point sur une ligne.
        Retourne t tel que projection = line_start + t * (line_end - line_start)
        """
        line_vec = line_end - line_start
        point_vec = point - line_start
        line_len_sq = line_vec.magnitude_squared()
        
        if line_len_sq == 0:
            return 0
        
        return point_vec.dot(line_vec) / line_len_sq


class Polygon:
    """Polygone 2D optimisé."""
    
    def __init__(self, points: List[Tuple[float, float]]):
        self.points = [Vector(x, y) for x, y in points]
    
    def area(self) -> float:
        """Calcule l'aire du polygone (formule de Shoelace)."""
        n = len(self.points)
        if n < 3:
            return 0
        
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.points[i].x * self.points[j].y
            area -= self.points[j].x * self.points[i].y
        
        return abs(area) / 2.0
    
    def perimeter(self) -> float:
        """Calcule le périmètre du polygone."""
        n = len(self.points)
        if n < 2:
            return 0
        
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            perimeter += self.points[i].distance_to(self.points[j])
        
        return perimeter
    
    def centroid(self) -> Vector:
        """Centre de masse du polygone."""
        n = len(self.points)
        if n == 0:
            return Vector(0, 0)
        
        cx = sum(p.x for p in self.points) / n
        cy = sum(p.y for p in self.points) / n
        return Vector(cx, cy)
    
    def point_inside(self, point: Vector) -> bool:
        """Test point dans polygone (ray casting)."""
        n = len(self.points)
        inside = False
        
        p1x, p1y = self.points[0].x, self.points[0].y
        
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n].x, self.points[i % n].y
            
            if point.y > min(p1y, p2y):
                if point.y <= max(p1y, p2y):
                    if point.x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (point.y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or point.x <= xinters:
                            inside = not inside
            
            p1x, p1y = p2x, p2y
        
        return inside
    
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Boîte englobante (min_x, min_y, max_x, max_y)."""
        if not self.points:
            return 0, 0, 0, 0
        
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        
        return min(xs), min(ys), max(xs), max(ys)
    
    def is_convex(self) -> bool:
        """Vérifie si le polygone est convexe."""
        n = len(self.points)
        if n < 3:
            return False
        
        sign = None
        
        for i in range(n):
            v1 = self.points[i]
            v2 = self.points[(i + 1) % n]
            v3 = self.points[(i + 2) % n]
            
            cross = (v2 - v1).cross(v3 - v2)
            
            if cross != 0:
                if sign is None:
                    sign = cross > 0
                elif (cross > 0) != sign:
                    return False
        
        return True


class Circle:
    """Cercle 2D."""
    
    def __init__(self, center: Tuple[float, float], radius: float):
        self.center = Vector(center[0], center[1])
        self.radius = radius
    
    def area(self) -> float:
        """Aire du cercle."""
        return math.pi * self.radius * self.radius
    
    def perimeter(self) -> float:
        """Périmètre du cercle."""
        return 2 * math.pi * self.radius
    
    def point_inside(self, point: Tuple[float, float]) -> bool:
        """Teste si un point est dans le cercle."""
        p = Vector(point[0], point[1])
        return self.center.distance_to_squared(p) <= self.radius * self.radius
    
    def intersects_circle(self, other: 'Circle') -> bool:
        """Teste l'intersection avec un autre cercle."""
        dist = self.center.distance_to(other.center)
        return dist <= (self.radius + other.radius)
    
    def intersects_point(self, point: Tuple[float, float], tolerance: float = 0) -> bool:
        """Teste l'intersection avec un point."""
        p = Vector(point[0], point[1])
        dist = self.center.distance_to(p)
        return abs(dist - self.radius) <= tolerance


def optimal_interpolation_points(start: Vector, end: Vector, 
                                 max_distance: float) -> List[Vector]:
    """Génère des points interpolés optimaux entre deux points."""
    distance = start.distance_to(end)
    
    if distance <= max_distance:
        return [start, end]
    
    num_segments = int(math.ceil(distance / max_distance))
    points = []
    
    for i in range(num_segments + 1):
        t = i / num_segments
        point = Vector(
            FastMath.lerp(start.x, end.x, t),
            FastMath.lerp(start.y, end.y, t)
        )
        points.append(point)
    
    return points
