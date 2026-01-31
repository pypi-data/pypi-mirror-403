import yaml
from portier.utils import CONFIG_FILE, ensure_portier_dir


DEFAULT_CONFIG = {
    'range': {
        'start': 3000,
        'end': 3999
    },
    'categories': {},
    'default_category': None
}


class Config:
    def __init__(self):
        self.path = CONFIG_FILE

    def create_default(self):
        """Crée le fichier de configuration par défaut"""
        ensure_portier_dir()
        self.save(DEFAULT_CONFIG)

    def load(self):
        """Charge la configuration"""
        if not self.path.exists():
            return DEFAULT_CONFIG
        with open(self.path, 'r') as f:
            return yaml.safe_load(f)

    def save(self, data):
        """Sauvegarde la configuration"""
        ensure_portier_dir()
        with open(self.path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_range(self, category=None):
        """Retourne la plage de ports pour une catégorie"""
        config = self.load()

        if category:
            categories = config.get('categories', {})
            if category in categories:
                return categories[category]['range']
            else:
                raise ValueError(f"Catégorie '{category}' inconnue")

        return [config['range']['start'], config['range']['end']]

    def add_category(self, name, start, end, description=None):
        """Ajoute une nouvelle catégorie"""
        config = self.load()

        if 'categories' not in config:
            config['categories'] = {}

        config['categories'][name] = {
            'range': [start, end],
            'description': description
        }
        self.save(config)

    def remove_category(self, name):
        """Supprime une catégorie"""
        config = self.load()

        if name in config.get('categories', {}):
            del config['categories'][name]
            self.save(config)
            return True
        return False

    def list_categories(self):
        """Liste toutes les catégories"""
        config = self.load()
        return config.get('categories', {})

    def set_range(self, start, end):
        """Modifie la plage de ports par défaut"""
        config = self.load()
        config['range']['start'] = start
        config['range']['end'] = end
        self.save(config)