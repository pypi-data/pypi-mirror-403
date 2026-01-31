"""Setup configuration for imgprocessor package."""

from setuptools import setup, find_packages
from pathlib import Path
import os
import sys
import subprocess

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Compiler automatiquement les modules C/C++ si disponibles
def compile_cpp_modules():
    """Compile les modules C/C++ optimisés si CMake et compilateur sont disponibles."""
    cpp_dir = Path(__file__).parent / "imgprocessor" / "cpp"
    cpp_build_script = cpp_dir / "build_cpp.py"
    
    if cpp_build_script.exists():
        try:
            print("\n🚀 Tentative de compilation des modules C/C++...")
            subprocess.run([sys.executable, str(cpp_build_script)], check=False)
            print("✓ Compilation C/C++ terminée (ou utilisation du fallback Python)")
        except Exception as e:
            print(f"⚠️  Impossible de compiler les modules C/C++: {e}")
            print("   Le package fonctionnera en mode pur Python (performances réduites)")

# Compile les modules C/C++ pendant l'installation
if os.environ.get('SKIPPING_CPP_BUILD', '0') == '0':
    compile_cpp_modules()

setup(
    name="image-processor-lite",
    version="1.0.5",
    author="ImageProcessor Team",
    description="Package modulaire de traitement et d'analyse d'images avec modules C/C++ optimisés",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Maik-start/image-processor-lite",
    packages=find_packages(),
    package_data={
        "imgprocessor": [
            "cpp/build/*",
            "cpp/*.py",
            "cpp/*.cpp",
            "cpp/CMakeLists.txt",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.8",
    install_requires=[
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
    ],
    extras_require={
        "text_detection": [
            "easyocr>=1.6.0",
        ],
        "text_detection_tesseract": [
            "pytesseract>=0.3.10",
        ],
        "optimization": [
            "cmake>=3.10",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/Maik-start/image-processor-lite/issues",
        "Source": "https://github.com/Maik-start/image-processor-lite",
        "Documentation": "https://github.com/Maik-start/image-processor-lite/wiki",
    },
    keywords="image processing opencv computer vision optimization",
    zip_safe=False,
)
