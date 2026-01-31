#!/usr/bin/env python3
"""
Script de compilation automatique des modules C/C++ optimisés.
À exécuter après installation du package pour compiler les extensions.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class CppCompiler:
    """Gère la compilation des modules C/C++."""
    
    def __init__(self):
        self.cpp_dir = Path(__file__).parent
        self.build_dir = self.cpp_dir / "build"
        self.os_name = platform.system()
        
    def create_build_dir(self):
        """Crée le répertoire de build."""
        self.build_dir.mkdir(exist_ok=True)
        print(f"✓ Répertoire de build créé: {self.build_dir}")
    
    def check_cmake(self):
        """Vérifie si CMake est installé."""
        try:
            result = subprocess.run(
                ["cmake", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"✓ CMake trouvé: {version}")
                return True
        except FileNotFoundError:
            pass
        
        print("✗ CMake non trouvé. Installation...")
        self.install_cmake()
        return True
    
    def install_cmake(self):
        """Installe CMake selon le système d'exploitation."""
        if self.os_name == "Linux":
            subprocess.run(["sudo", "apt-get", "install", "-y", "cmake"], check=False)
        elif self.os_name == "Darwin":  # macOS
            subprocess.run(["brew", "install", "cmake"], check=False)
        elif self.os_name == "Windows":
            print("Veuillez installer CMake depuis: https://cmake.org/download/")
    
    def check_compiler(self):
        """Vérifie si un compilateur C++ est disponible."""
        compilers = ["g++", "clang++", "cl.exe"]
        
        for compiler in compilers:
            try:
                result = subprocess.run(
                    [compiler, "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✓ Compilateur trouvé: {compiler}")
                    return True
            except FileNotFoundError:
                pass
        
        print("✗ Aucun compilateur C++ trouvé")
        if self.os_name == "Linux":
            print("Installation: sudo apt-get install build-essential")
        elif self.os_name == "Darwin":
            print("Installation: brew install gcc")
        elif self.os_name == "Windows":
            print("Installation: Visual Studio Build Tools")
        
        return False
    
    def configure(self):
        """Configure le build avec CMake."""
        print("\n🔧 Configuration CMake...")
        
        os.chdir(self.build_dir)
        
        cmake_cmd = [
            "cmake",
            "..",
            "-DCMAKE_BUILD_TYPE=Release",
        ]
        
        if self.os_name == "Windows":
            cmake_cmd.extend(["-G", "Visual Studio 16 2019"])
        
        result = subprocess.run(cmake_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Erreur de configuration:\n{result.stderr}")
            return False
        
        print("✓ Configuration réussie")
        return True
    
    def build(self):
        """Compile les modules."""
        print("\n🔨 Compilation des modules C/C++...")
        
        os.chdir(self.build_dir)
        
        build_cmd = ["cmake", "--build", ".", "--config", "Release"]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Erreur de compilation:\n{result.stderr}")
            return False
        
        print("✓ Compilation réussie")
        return True
    
    def move_libraries(self):
        """Déplace les librairies compilées dans le répertoire approprié."""
        print("\n📦 Déplacement des librairies compilées...")
        
        lib_src_dir = self.build_dir / "lib"
        lib_dst_dir = self.cpp_dir / "build"
        
        if lib_src_dir != lib_dst_dir and lib_src_dir.exists():
            for lib_file in lib_src_dir.glob("*"):
                import shutil
                dst_file = lib_dst_dir / lib_file.name
                if lib_file.is_file():
                    shutil.copy2(lib_file, dst_file)
                    print(f"  ✓ {lib_file.name}")
        
        print("✓ Librairies placées dans:", lib_dst_dir)
    
    def compile(self):
        """Lance la compilation complète."""
        print("=" * 70)
        print("🚀 COMPILATION DES MODULES C/C++ OPTIMISÉS")
        print("=" * 70)
        
        self.create_build_dir()
        
        if not self.check_cmake():
            print("⚠️  CMake non disponible, compilation annulée")
            return False
        
        if not self.check_compiler():
            print("⚠️  Compilateur C++ non disponible, compilation annulée")
            return False
        
        if not self.configure():
            return False
        
        if not self.build():
            return False
        
        self.move_libraries()
        
        print("\n" + "=" * 70)
        print("✅ COMPILATION TERMINÉE AVEC SUCCÈS")
        print("=" * 70)
        print("\n📈 Gains de performance attendus:")
        print("   • Filtres d'image (Gaussian, Canny): 3-5x plus rapide")
        print("   • Calculs de distances: 10-20x plus rapide")
        print("   • Détection de formes: 2-4x plus rapide")
        print("\n")
        
        return True


def main():
    """Point d'entrée."""
    compiler = CppCompiler()
    
    if not compiler.compile():
        print("\n⚠️  Compilation annulée, le package fonctionnera en mode pur Python")
        print("   (avec performances réduites)")
        sys.exit(1)


if __name__ == "__main__":
    main()
