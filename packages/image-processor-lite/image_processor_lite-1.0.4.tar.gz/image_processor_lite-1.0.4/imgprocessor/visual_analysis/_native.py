"""Native extension loader and fallbacks for visual analysis.

This module attempts to import a compiled `_native` extension (C/C++).
If it's not available, the functions will raise `NotImplementedError` so
the pure-Python fallbacks in `analyzer.py` can be used.
"""
try:
    from . import _native as _cext  # compiled extension (optional)
except Exception:
    _cext = None


def segment_by_color(image, k=5):
    """Delegate to compiled `segment_by_color` if available.
    Raises NotImplementedError when no native implementation.
    """
    if _cext and hasattr(_cext, 'segment_by_color'):
        return _cext.segment_by_color(image, k)
    raise NotImplementedError('Native segment_by_color not built')


def compute_chromatic_stability(hsv, mask):
    """Delegate to compiled `compute_chromatic_stability` if available.
    Raises NotImplementedError when no native implementation.
    """
    if _cext and hasattr(_cext, 'compute_chromatic_stability'):
        return _cext.compute_chromatic_stability(hsv, mask)
    raise NotImplementedError('Native compute_chromatic_stability not built')
