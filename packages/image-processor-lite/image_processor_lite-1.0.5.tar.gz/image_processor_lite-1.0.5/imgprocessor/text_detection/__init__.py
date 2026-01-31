"""Text detection module for ImageProcessor package - OPTIMIZED VERSION."""

# Utiliser la version optimisée par défaut
try:
    from .detector_optimized import TextDetector, TextDetectorOptimized, TextRegion
except ImportError:
    # Fallback sur l'ancienne version si detector_optimized n'existe pas
    from .detector import TextDetector, TextRegion
    TextDetectorOptimized = TextDetector

__all__ = ['TextDetector', 'TextDetectorOptimized', 'TextRegion']
