import json
from datetime import datetime
from portier.utils import REGISTRY_FILE, ensure_portier_dir
from portier.config import Config


class Registry:
    def __init__(self):
        self.path = REGISTRY_FILE

    def create_empty(self):
        """Crée un registre vide"""
        ensure_portier_dir()
        self.save({'apps': {}})

    def load(self):
        """Charge le registre"""
        if not self.path.exists():
            return {'apps': {}}
        with open(self.path, 'r') as f:
            return json.load(f)

    def save(self, data):
        """Sauvegarde le registre"""
        ensure_portier_dir()
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def add(self, name, port, category=None):
        """Ajoute une app au registre"""
        data = self.load()
        data['apps'][name] = {
            'port': port,
            'category': category,
            'created_at': datetime.now().isoformat()
        }
        self.save(data)

    def remove(self, name):
        """Supprime une app du registre"""
        data = self.load()
        if name in data['apps']:
            del data['apps'][name]
            self.save(data)
            return True
        return False

    def get_all(self):
        """Retourne toutes les apps"""
        data = self.load()
        return data.get('apps', {})

    def get_used_ports(self):
        """Retourne la liste des ports utilisés"""
        data = self.load()
        return [app['port'] for app in data['apps'].values()]

    def get_app_by_port(self, port):
        """Trouve l'app qui utilise un port"""
        data = self.load()
        for name, app in data['apps'].items():
            if app['port'] == port:
                return name
        return None

    def get_next_available_port(self, category=None):
        """Trouve le prochain port disponible"""
        config = Config()
        start, end = config.get_range(category)
        used_ports = self.get_used_ports()

        for port in range(start, end + 1):
            if port not in used_ports:
                return port

        raise Exception(f"Plus de ports disponibles dans la plage {start}-{end}")

    def is_port_available(self, port):
        """Vérifie si un port est disponible dans le registre"""
        return port not in self.get_used_ports()