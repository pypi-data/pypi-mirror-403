from pathlib import Path

# Dossier de configuration de portier
PORTIER_DIR = Path.home() / '.portier'
CONFIG_FILE = PORTIER_DIR / 'config.yaml'
REGISTRY_FILE = PORTIER_DIR / 'registry.json'


def ensure_portier_dir():
    """Crée le dossier ~/.portier s'il n'existe pas"""
    PORTIER_DIR.mkdir(exist_ok=True)


def is_initialized():
    """Vérifie si portier est initialisé"""
    return CONFIG_FILE.exists() and REGISTRY_FILE.exists()