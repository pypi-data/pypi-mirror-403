"""
Configuration centralisée pour les modules de traitement d'images.
Permet l'activation/désactivation indépendante de chaque fonctionnalité.
"""

from dataclasses import dataclass, field
from typing import Dict
import json
from pathlib import Path


@dataclass
class ModuleConfig:
    """Classe de configuration pour chaque module."""
    enabled: bool = True
    options: Dict = field(default_factory=dict)


class ImageProcessorConfig:
    """
    Gestionnaire de configuration centralisé pour ImageProcessor.
    Permet d'activer/désactiver chaque module indépendamment.
    """

    def __init__(self, config_file: str = None):
        """
        Initialise la configuration.
        
        Args:
            config_file: Chemin optionnel vers un fichier de configuration JSON
        """
        self.modules: Dict[str, ModuleConfig] = {
            'text_detection': ModuleConfig(enabled=False, options={
                'language': ['fra', 'eng'],
                'engine': 'easyocr'  # ou 'tesseract'
            }),
            'shape_detection': ModuleConfig(enabled=False, options={
                'detect_circles': True,
                'detect_rectangles': True,
                'detect_polygons': True,
                'min_contour_area': 50
            }),
            'distance_measurement': ModuleConfig(enabled=False, options={
                'unit': 'pixels',  # ou 'mm', 'cm'
                'precision': 2
            }),
            'visual_analysis': ModuleConfig(enabled=False, options={
                'analyze_brightness': True,
                'analyze_contrast': True,
                'analyze_hue': True,
                'bins': 256
            })
        }
        
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)
    
    def enable_module(self, module_name: str, enabled: bool = True) -> None:
        """Active ou désactive un module."""
        if module_name in self.modules:
            self.modules[module_name].enabled = enabled
        else:
            raise ValueError(f"Module '{module_name}' non reconnu")
    
    def is_module_enabled(self, module_name: str) -> bool:
        """Vérifie si un module est activé."""
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' non reconnu")
        return self.modules[module_name].enabled
    
    def set_module_options(self, module_name: str, options: Dict) -> None:
        """Définit les options pour un module."""
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' non reconnu")
        self.modules[module_name].options.update(options)
    
    def get_module_options(self, module_name: str) -> Dict:
        """Récupère les options d'un module."""
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' non reconnu")
        return self.modules[module_name].options
    
    def disable_all_modules(self) -> None:
        """Désactive tous les modules."""
        for module in self.modules.values():
            module.enabled = False
    
    def enable_all_modules(self) -> None:
        """Active tous les modules."""
        for module in self.modules.values():
            module.enabled = True
    
    def save_to_file(self, config_file: str) -> None:
        """Sauvegarde la configuration en JSON."""
        config_dict = {
            name: {
                'enabled': config.enabled,
                'options': config.options
            }
            for name, config in self.modules.items()
        }
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def load_from_file(self, config_file: str) -> None:
        """Charge la configuration depuis un fichier JSON."""
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        
        for module_name, config in config_dict.items():
            if module_name in self.modules:
                self.modules[module_name].enabled = config.get('enabled', True)
                self.modules[module_name].options.update(config.get('options', {}))
    
    def get_status(self) -> Dict:
        """Retourne le statut de tous les modules."""
        return {
            name: {
                'enabled': config.enabled,
                'options': config.options
            }
            for name, config in self.modules.items()
        }
    
    def __repr__(self) -> str:
        return f"ImageProcessorConfig(modules={list(self.modules.keys())})"
