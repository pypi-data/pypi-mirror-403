import docker
from docker.errors import DockerException


class DockerScanner:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.available = True
        except DockerException:
            self.client = None
            self.available = False

    def is_available(self):
        """Vérifie si Docker est accessible"""
        return self.available

    def get_running_containers(self):
        """Liste les conteneurs avec leurs ports exposés"""
        if not self.available:
            return []

        containers = self.client.containers.list()
        result = []

        for container in containers:
            ports = container.ports
            for container_port, host_bindings in ports.items():
                if host_bindings:
                    for binding in host_bindings:
                        result.append({
                            'name': container.name,
                            'host_port': int(binding['HostPort']),
                            'container_port': container_port
                        })

        return result

    def is_container_running(self, name):
        """Vérifie si un conteneur existe et tourne"""
        if not self.available:
            return False

        try:
            container = self.client.containers.get(name)
            return container.status == 'running'
        except docker.errors.NotFound:
            return False

    def is_port_in_use(self, port):
        """Vérifie si un port est utilisé par un conteneur Docker"""
        containers = self.get_running_containers()
        return any(c['host_port'] == port for c in containers)

    def get_container_by_port(self, port):
        """Trouve le conteneur qui utilise un port"""
        containers = self.get_running_containers()
        for c in containers:
            if c['host_port'] == port:
                return c['name']
        return None