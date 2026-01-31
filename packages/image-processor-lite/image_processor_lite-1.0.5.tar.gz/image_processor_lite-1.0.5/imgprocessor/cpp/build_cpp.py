#!/usr/bin/env python3
"""
Script de compilation automatique des modules C/C++ optimisés.
À exécuter après installation du package pour compiler les extensions.
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path

# Configure logging (silent by default, errors only)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class CppCompiler:
    """Gère la compilation des modules C/C++."""
    
    def __init__(self):
        self.cpp_dir = Path(__file__).parent
        self.build_dir = self.cpp_dir / "build"
        self.os_name = platform.system()
        
    def create_build_dir(self):
        """Crée le répertoire de build."""
        self.build_dir.mkdir(exist_ok=True)
    
    def check_cmake(self):
        """Vérifie si CMake est installé."""
        try:
            result = subprocess.run(
                ["cmake", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def check_compiler(self):
        """Vérifie si un compilateur C++ est disponible."""
        compilers = ["g++", "clang++", "cl.exe"]
        
        for compiler in compilers:
            try:
                result = subprocess.run(
                    [compiler, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return False
    
    def configure(self):
        """Configure le build avec CMake."""
        try:
            os.chdir(self.build_dir)
            
            cmake_cmd = [
                "cmake",
                "..",
                "-DCMAKE_BUILD_TYPE=Release",
            ]
            
            if self.os_name == "Windows":
                cmake_cmd.extend(["-G", "Visual Studio 16 2019"])
            
            result = subprocess.run(cmake_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"CMake configuration failed:\n{result.stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return False
    
    def build(self):
        """Compile les modules."""
        try:
            os.chdir(self.build_dir)
            
            build_cmd = ["cmake", "--build", ".", "--config", "Release"]
            
            result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Build failed:\n{result.stderr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def move_libraries(self):
        """Déplace les librairies compilées dans le répertoire approprié."""
        try:
            lib_src_dir = self.build_dir / "lib"
            lib_dst_dir = self.cpp_dir / "build"
            
            if lib_src_dir != lib_dst_dir and lib_src_dir.exists():
                import shutil
                for lib_file in lib_src_dir.glob("*"):
                    if lib_file.is_file():
                        dst_file = lib_dst_dir / lib_file.name
                        shutil.copy2(lib_file, dst_file)
        except Exception as e:
            logger.error(f"Library move error: {e}")
    
    def compile(self):
        """Lance la compilation complète."""
        try:
            self.create_build_dir()
            
            if not self.check_cmake():
                logger.warning("CMake not found, skipping C/C++ compilation")
                return False
            
            if not self.check_compiler():
                logger.warning("C++ compiler not found, skipping compilation")
                return False
            
            if not self.configure():
                return False
            
            if not self.build():
                return False
            
            self.move_libraries()
            
            return True
        except Exception as e:
            logger.error(f"Compilation error: {e}")
            return False


def main():
    """Point d'entrée."""
    compiler = CppCompiler()
    
    if not compiler.compile():
        logger.warning("C/C++ compilation skipped - using pure Python (reduced performance)")
        sys.exit(1)


if __name__ == "__main__":
    main()
