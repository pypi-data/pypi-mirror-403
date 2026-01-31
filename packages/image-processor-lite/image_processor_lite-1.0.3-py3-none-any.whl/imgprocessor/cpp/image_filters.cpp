#include <cmath>
#include <vector>
#include <algorithm>
#include <cstring>

// Structure pour représenter une image
struct Image {
    int width;
    int height;
    int channels;
    unsigned char* data;
};

// ============================================================================
// GAUSSIAN BLUR - Opération critique, très utilisée
// ============================================================================

extern "C" {
    /**
     * Applique un filtre Gaussien à une image.
     * Optimisé avec séparation horizontale/verticale (O(n) au lieu O(n²))
     */
    void gaussian_blur(unsigned char* image_data, int width, int height, 
                       int channels, int kernel_size, float sigma,
                       unsigned char* output) {
        // Créer le kernel gaussien 1D
        int radius = kernel_size / 2;
        std::vector<float> kernel(kernel_size);
        float sum = 0.0f;
        float sigma_sq_2 = 2.0f * sigma * sigma;
        
        for (int i = -radius; i <= radius; i++) {
            float val = std::exp(-(i * i) / sigma_sq_2);
            kernel[i + radius] = val;
            sum += val;
        }
        
        // Normaliser le kernel
        for (int i = 0; i < kernel_size; i++) {
            kernel[i] /= sum;
        }
        
        // Passe horizontale
        std::vector<float> horizontal(width * height * channels);
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                for (int c = 0; c < channels; c++) {
                    float result = 0.0f;
                    for (int k = -radius; k <= radius; k++) {
                        int nx = x + k;
                        if (nx >= 0 && nx < width) {
                            result += image_data[(y * width + nx) * channels + c] * kernel[k + radius];
                        }
                    }
                    horizontal[(y * width + x) * channels + c] = result;
                }
            }
        }
        
        // Passe verticale
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                for (int c = 0; c < channels; c++) {
                    float result = 0.0f;
                    for (int k = -radius; k <= radius; k++) {
                        int ny = y + k;
                        if (ny >= 0 && ny < height) {
                            result += horizontal[(ny * width + x) * channels + c] * kernel[k + radius];
                        }
                    }
                    output[(y * width + x) * channels + c] = (unsigned char)std::max(0.0f, std::min(255.0f, result));
                }
            }
        }
    }
    
    // ============================================================================
    // CANNY EDGE DETECTION - Critère pour détection de formes
    // ============================================================================
    
    /**
     * Convertit une image BGR en niveaux de gris.
     */
    void bgr_to_grayscale(unsigned char* image_data, int width, int height, 
                         unsigned char* output) {
        for (int i = 0; i < width * height; i++) {
            // Formule standard: 0.299*R + 0.587*G + 0.114*B
            float r = image_data[i * 3];
            float g = image_data[i * 3 + 1];
            float b = image_data[i * 3 + 2];
            output[i] = (unsigned char)(0.299f * r + 0.587f * g + 0.114f * b);
        }
    }
    
    /**
     * Calcule les gradients (détecteur Sobel).
     */
    void sobel_gradient(unsigned char* image_data, int width, int height,
                       float* gx, float* gy) {
        // Kernels Sobel
        int sobel_x[3][3] = {
            {-1, 0, 1},
            {-2, 0, 2},
            {-1, 0, 1}
        };
        
        int sobel_y[3][3] = {
            {-1, -2, -1},
            {0, 0, 0},
            {1, 2, 1}
        };
        
        for (int y = 1; y < height - 1; y++) {
            for (int x = 1; x < width - 1; x++) {
                float grad_x = 0.0f;
                float grad_y = 0.0f;
                
                for (int ky = -1; ky <= 1; ky++) {
                    for (int kx = -1; kx <= 1; kx++) {
                        int pixel = image_data[(y + ky) * width + (x + kx)];
                        grad_x += pixel * sobel_x[ky + 1][kx + 1];
                        grad_y += pixel * sobel_y[ky + 1][kx + 1];
                    }
                }
                
                gx[y * width + x] = grad_x;
                gy[y * width + x] = grad_y;
            }
        }
    }
    
    /**
     * Applique la détection de contours Canny.
     */
    void canny_edges(unsigned char* image_data, int width, int height,
                    float low_threshold, float high_threshold,
                    unsigned char* output) {
        // Allocations
        std::vector<float> gx(width * height);
        std::vector<float> gy(width * height);
        std::vector<float> magnitude(width * height);
        std::vector<float> angle(width * height);
        std::vector<unsigned char> suppressed(width * height);
        
        // Calcul des gradients
        sobel_gradient(image_data, width, height, gx.data(), gy.data());
        
        // Calcul de la magnitude et angle
        for (int i = 0; i < width * height; i++) {
            magnitude[i] = std::sqrt(gx[i] * gx[i] + gy[i] * gy[i]);
            angle[i] = std::atan2(gy[i], gx[i]);
        }
        
        // Non-maximum suppression
        for (int y = 1; y < height - 1; y++) {
            for (int x = 1; x < width - 1; x++) {
                float angle_deg = (angle[y * width + x] * 180.0f / 3.14159265f) + 180.0f;
                float mag = magnitude[y * width + x];
                
                float mag1 = 0, mag2 = 0;
                
                if ((angle_deg >= 0 && angle_deg < 22.5) || (angle_deg >= 157.5 && angle_deg <= 180)) {
                    mag1 = magnitude[y * width + (x + 1)];
                    mag2 = magnitude[y * width + (x - 1)];
                } else if (angle_deg >= 22.5 && angle_deg < 67.5) {
                    mag1 = magnitude[(y + 1) * width + (x - 1)];
                    mag2 = magnitude[(y - 1) * width + (x + 1)];
                } else if (angle_deg >= 67.5 && angle_deg < 112.5) {
                    mag1 = magnitude[(y + 1) * width + x];
                    mag2 = magnitude[(y - 1) * width + x];
                } else if (angle_deg >= 112.5 && angle_deg < 157.5) {
                    mag1 = magnitude[(y + 1) * width + (x + 1)];
                    mag2 = magnitude[(y - 1) * width + (x - 1)];
                }
                
                if (mag >= mag1 && mag >= mag2) {
                    suppressed[y * width + x] = (unsigned char)mag;
                } else {
                    suppressed[y * width + x] = 0;
                }
            }
        }
        
        // Double thresholding et edge tracking by hysteresis
        std::vector<unsigned char> edges(width * height);
        for (int i = 0; i < width * height; i++) {
            if (suppressed[i] >= high_threshold) {
                edges[i] = 255;
            } else if (suppressed[i] < low_threshold) {
                edges[i] = 0;
            } else {
                edges[i] = 127; // Weak edge
            }
        }
        
        // Hysteresis
        for (int y = 1; y < height - 1; y++) {
            for (int x = 1; x < width - 1; x++) {
                if (edges[y * width + x] == 127) {
                    bool strong_nearby = false;
                    for (int ky = -1; ky <= 1; ky++) {
                        for (int kx = -1; kx <= 1; kx++) {
                            if (edges[(y + ky) * width + (x + kx)] == 255) {
                                strong_nearby = true;
                                break;
                            }
                        }
                        if (strong_nearby) break;
                    }
                    edges[y * width + x] = strong_nearby ? 255 : 0;
                }
            }
        }
        
        std::memcpy(output, edges.data(), width * height);
    }
    
    // ============================================================================
    // CONTOUR DETECTION - Très critique pour shape_detection
    // ============================================================================
    
    /**
     * Détecte les contours en parcourant les pixels de contour (tracé)
     */
    int find_contours(unsigned char* binary_image, int width, int height,
                     int* contour_buffer, int max_contour_size) {
        int contour_count = 0;
        std::vector<bool> visited(width * height, false);
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int idx = y * width + x;
                if (binary_image[idx] > 128 && !visited[idx]) {
                    // Début d'un nouveau contour
                    int start_x = x, start_y = y;
                    int cx = x, cy = y;
                    int dir = 0; // Direction (0-7, sens horaire)
                    
                    int contour_points = 0;
                    int px = x, py = y;
                    
                    do {
                        visited[py * width + px] = true;
                        
                        // Ajouter le point au buffer
                        if (contour_count * 2 + contour_points * 2 + 1 < max_contour_size) {
                            contour_buffer[contour_count * 2 + contour_points * 2] = px;
                            contour_buffer[contour_count * 2 + contour_points * 2 + 1] = py;
                            contour_points++;
                        }
                        
                        // Chercher le prochain pixel du contour
                        bool found = false;
                        for (int d = 0; d < 8; d++) {
                            int nd = (dir + d) % 8;
                            int nx = px, ny = py;
                            
                            // Directions: droite, bas-droite, bas, bas-gauche, etc.
                            switch (nd) {
                                case 0: nx++; break;
                                case 1: nx++; ny++; break;
                                case 2: ny++; break;
                                case 3: nx--; ny++; break;
                                case 4: nx--; break;
                                case 5: nx--; ny--; break;
                                case 6: ny--; break;
                                case 7: nx++; ny--; break;
                            }
                            
                            if (nx >= 0 && nx < width && ny >= 0 && ny < height &&
                                binary_image[ny * width + nx] > 128) {
                                px = nx;
                                py = ny;
                                dir = nd;
                                found = true;
                                break;
                            }
                        }
                        
                        if (!found || (px == start_x && py == start_y && contour_points > 3)) {
                            break;
                        }
                    } while (true);
                    
                    if (contour_points > 2) {
                        contour_count++;
                    }
                }
            }
        }
        
        return contour_count;
    }
    
    // ============================================================================
    // FAST CONVOLUTION - Pour filtres génériques
    // ============================================================================
    
    /**
     * Convolution générique optimisée.
     */
    void convolve_2d(unsigned char* image_data, int width, int height,
                    float* kernel, int kernel_size,
                    unsigned char* output) {
        int radius = kernel_size / 2;
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                float result = 0.0f;
                
                for (int ky = -radius; ky <= radius; ky++) {
                    for (int kx = -radius; kx <= radius; kx++) {
                        int ny = y + ky;
                        int nx = x + kx;
                        
                        if (ny >= 0 && ny < height && nx >= 0 && nx < width) {
                            result += image_data[ny * width + nx] * 
                                    kernel[(ky + radius) * kernel_size + (kx + radius)];
                        }
                    }
                }
                
                output[y * width + x] = (unsigned char)std::max(0.0f, std::min(255.0f, result));
            }
        }
    }
}
