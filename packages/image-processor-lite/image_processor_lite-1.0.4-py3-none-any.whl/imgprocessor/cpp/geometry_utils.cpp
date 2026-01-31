#include <cmath>
#include <vector>
#include <algorithm>
#include <cstring>

// ============================================================================
// DISTANCE CALCULATIONS - Très critiques, calculs répétés
// ============================================================================

extern "C" {
    /**
     * Distance euclidienne entre deux points.
     * Opération ultra-rapide et critique.
     */
    float euclidean_distance(float x1, float y1, float x2, float y2) {
        float dx = x2 - x1;
        float dy = y2 - y1;
        return std::sqrt(dx * dx + dy * dy);
    }
    
    /**
     * Distance euclidienne au carré (plus rapide, pas de sqrt).
     */
    float euclidean_distance_squared(float x1, float y1, float x2, float y2) {
        float dx = x2 - x1;
        float dy = y2 - y1;
        return dx * dx + dy * dy;
    }
    
    /**
     * Distance de Manhattan (L1).
     */
    float manhattan_distance(float x1, float y1, float x2, float y2) {
        return std::abs(x2 - x1) + std::abs(y2 - y1);
    }
    
    /**
     * Distance de Chebyshev (Linf).
     */
    float chebyshev_distance(float x1, float y1, float x2, float y2) {
        return std::max(std::abs(x2 - x1), std::abs(y2 - y1));
    }
    
    // ============================================================================
    // CONTOUR OPERATIONS
    // ============================================================================
    
    /**
     * Calcule la distance minimale entre deux contours.
     * Contour1 et Contour2 sont des tableaux de points (x1, y1, x2, y2, ...)
     */
    struct ClosestPoints {
        float distance;
        float from_x, from_y;
        float to_x, to_y;
    };
    
    ClosestPoints contour_to_contour_distance(float* contour1, int size1,
                                            float* contour2, int size2) {
        ClosestPoints result = {99999.0f, 0, 0, 0, 0};
        
        for (int i = 0; i < size1; i += 2) {
            for (int j = 0; j < size2; j += 2) {
                float dist = euclidean_distance(
                    contour1[i], contour1[i + 1],
                    contour2[j], contour2[j + 1]
                );
                
                if (dist < result.distance) {
                    result.distance = dist;
                    result.from_x = contour1[i];
                    result.from_y = contour1[i + 1];
                    result.to_x = contour2[j];
                    result.to_y = contour2[j + 1];
                }
            }
        }
        
        return result;
    }
    
    /**
     * Point dans polygone (algoritme ray casting).
     */
    int point_in_polygon(float px, float py, float* polygon, int size) {
        int count = 0;
        
        for (int i = 0; i < size; i += 2) {
            float x1 = polygon[i];
            float y1 = polygon[i + 1];
            float x2 = polygon[(i + 2) % size];
            float y2 = polygon[(i + 3) % size];
            
            if ((y1 <= py && py < y2) || (y2 <= py && py < y1)) {
                float xinters = (x2 - x1) * (py - y1) / (y2 - y1) + x1;
                if (px < xinters) {
                    count++;
                }
            }
        }
        
        return count % 2;
    }
    
    /**
     * Distance d'un point au polygone (< 0 intérieur, > 0 extérieur, 0 sur le bord)
     */
    float point_polygon_distance(float px, float py, float* polygon, int size) {
        float min_dist = 99999.0f;
        
        for (int i = 0; i < size; i += 2) {
            float x1 = polygon[i];
            float y1 = polygon[i + 1];
            float x2 = polygon[(i + 2) % size];
            float y2 = polygon[(i + 3) % size];
            
            // Distance du point au segment
            float dx = x2 - x1;
            float dy = y2 - y1;
            float len_sq = dx * dx + dy * dy;
            
            if (len_sq == 0) {
                float d = euclidean_distance(px, py, x1, y1);
                min_dist = std::min(min_dist, d);
            } else {
                float t = std::max(0.0f, std::min(1.0f, 
                    ((px - x1) * dx + (py - y1) * dy) / len_sq));
                float proj_x = x1 + t * dx;
                float proj_y = y1 + t * dy;
                float d = euclidean_distance(px, py, proj_x, proj_y);
                min_dist = std::min(min_dist, d);
            }
        }
        
        // Signe selon position (inside/outside)
        int inside = point_in_polygon(px, py, polygon, size);
        return inside ? -min_dist : min_dist;
    }
    
    // ============================================================================
    // SHAPE ANALYSIS
    // ============================================================================
    
    /**
     * Calcule l'aire d'un polygone (formule de Shoelace).
     */
    float polygon_area(float* polygon, int size) {
        float area = 0.0f;
        
        for (int i = 0; i < size; i += 2) {
            float x1 = polygon[i];
            float y1 = polygon[i + 1];
            float x2 = polygon[(i + 2) % size];
            float y2 = polygon[(i + 3) % size];
            
            area += (x1 * y2 - x2 * y1);
        }
        
        return std::abs(area) / 2.0f;
    }
    
    /**
     * Calcule le périmètre d'un polygone.
     */
    float polygon_perimeter(float* polygon, int size) {
        float perimeter = 0.0f;
        
        for (int i = 0; i < size; i += 2) {
            float x1 = polygon[i];
            float y1 = polygon[i + 1];
            float x2 = polygon[(i + 2) % size];
            float y2 = polygon[(i + 3) % size];
            
            perimeter += euclidean_distance(x1, y1, x2, y2);
        }
        
        return perimeter;
    }
    
    /**
     * Trouve le centre de masse d'un polygone.
     */
    struct Point {
        float x, y;
    };
    
    Point polygon_centroid(float* polygon, int size) {
        float cx = 0.0f, cy = 0.0f;
        
        for (int i = 0; i < size; i += 2) {
            cx += polygon[i];
            cy += polygon[i + 1];
        }
        
        return {cx / (size / 2), cy / (size / 2)};
    }
    
    /**
     * Détecte si une forme est approximativement un rectangle.
     */
    int is_rectangle(float* polygon, int size, float angle_tolerance) {
        if (size != 8) return 0; // 4 points = 8 coordonnées
        
        // Vérifier si les 4 angles sont proches de 90 degrés
        int right_angles = 0;
        
        for (int i = 0; i < 4; i++) {
            float x1 = polygon[i * 2];
            float y1 = polygon[i * 2 + 1];
            float x2 = polygon[((i + 1) % 4) * 2];
            float y2 = polygon[((i + 1) % 4) * 2 + 1];
            float x3 = polygon[((i + 2) % 4) * 2];
            float y3 = polygon[((i + 2) % 4) * 2 + 1];
            
            // Vecteurs
            float v1x = x1 - x2, v1y = y1 - y2;
            float v2x = x3 - x2, v2y = y3 - y2;
            
            // Produit scalaire
            float dot = v1x * v2x + v1y * v2y;
            float angle = std::acos(dot / (euclidean_distance(0, 0, v1x, v1y) * 
                                          euclidean_distance(0, 0, v2x, v2y)));
            
            if (std::abs(angle - 3.14159265f / 2) < angle_tolerance) {
                right_angles++;
            }
        }
        
        return right_angles == 4 ? 1 : 0;
    }
    
    /**
     * Détecte si une forme est approximativement un cercle.
     */
    int is_circle(float* polygon, int size, float circularity_threshold) {
        float area = polygon_area(polygon, size);
        float perimeter = polygon_perimeter(polygon, size);
        
        // Circularity = 4π*area / perimeter²
        float circularity = 4 * 3.14159265f * area / (perimeter * perimeter);
        
        return circularity > circularity_threshold ? 1 : 0;
    }
    
    // ============================================================================
    // CONVEX HULL
    // ============================================================================
    
    /**
     * Algorithme Graham pour calculer l'enveloppe convexe.
     * Entrée: tableau de points [x1, y1, x2, y2, ...]
     * Sortie: indices des points de la convex hull
     */
    int convex_hull_graham(float* points, int num_points, 
                          int* hull_indices, int max_hull_size) {
        if (num_points < 3) {
            for (int i = 0; i < num_points; i++) {
                hull_indices[i] = i;
            }
            return num_points;
        }
        
        // Trouver le point avec y minimal (puis x minimal)
        int start = 0;
        for (int i = 1; i < num_points; i++) {
            if (points[i * 2 + 1] < points[start * 2 + 1] ||
                (points[i * 2 + 1] == points[start * 2 + 1] && 
                 points[i * 2] < points[start * 2])) {
                start = i;
            }
        }
        
        // Produit croisé entre les vecteurs p1->p2 et p1->p3
        auto cross = [&](int p1, int p2, int p3) -> float {
            float o1x = points[p2 * 2] - points[p1 * 2];
            float o1y = points[p2 * 2 + 1] - points[p1 * 2 + 1];
            float o2x = points[p3 * 2] - points[p1 * 2];
            float o2y = points[p3 * 2 + 1] - points[p1 * 2 + 1];
            return o1x * o2y - o1y * o2x;
        };
        
        // Trier par angle polaire
        std::vector<int> sorted_indices;
        for (int i = 0; i < num_points; i++) {
            if (i != start) sorted_indices.push_back(i);
        }
        
        std::sort(sorted_indices.begin(), sorted_indices.end(),
            [&](int a, int b) {
                float val = cross(start, a, b);
                if (val == 0) {
                    float da = euclidean_distance_squared(
                        points[start * 2], points[start * 2 + 1],
                        points[a * 2], points[a * 2 + 1]);
                    float db = euclidean_distance_squared(
                        points[start * 2], points[start * 2 + 1],
                        points[b * 2], points[b * 2 + 1]);
                    return da < db;
                }
                return val > 0;
            }
        );
        
        // Construire la hull
        std::vector<int> hull;
        hull.push_back(start);
        
        for (int idx : sorted_indices) {
            while (hull.size() > 1 && 
                   cross(hull[hull.size() - 2], hull.back(), idx) <= 0) {
                hull.pop_back();
            }
            hull.push_back(idx);
        }
        
        // Copier résultat
        int result_size = std::min((int)hull.size(), max_hull_size);
        for (int i = 0; i < result_size; i++) {
            hull_indices[i] = hull[i];
        }
        
        return result_size;
    }
}
