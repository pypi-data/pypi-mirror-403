import click
from rich.console import Console
from rich.table import Table

from portier import __version__
from portier.config import Config
from portier.registry import Registry
from portier.scanner import DockerScanner
from portier.utils import is_initialized

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name='portier')
def main():
    """Portier - Gestionnaire de ports pour vos applications Docker"""
    pass


@main.command()
def init():
    """Initialise portier"""
    if is_initialized():
        console.print("[yellow]Portier est déjà initialisé.[/yellow]")
        return

    config = Config()
    registry = Registry()

    config.create_default()
    registry.create_empty()

    console.print("[green]✓ Portier initialisé[/green]")
    console.print(f"  Plage par défaut : 3000-3999")
    console.print(f"  Config : ~/.portier/config.yaml")
    console.print(f"  Registre : ~/.portier/registry.json")


@main.command()
@click.argument('name')
@click.option('--category', '-c', default=None, help="Catégorie de l'app")
@click.option('--port', '-p', default=None, type=int, help="Port spécifique (optionnel)")
def add(name, category, port):
    """Attribue un port à une nouvelle app"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    registry = Registry()
    scanner = DockerScanner()

    # Vérifier si l'app existe déjà
    apps = registry.get_all()
    if name in apps:
        console.print(f"[red]Erreur : L'app '{name}' existe déjà (port {apps[name]['port']})[/red]")
        return

    # Trouver ou valider le port
    try:
        if port:
            # Port spécifié manuellement
            if not registry.is_port_available(port):
                app_using = registry.get_app_by_port(port)
                console.print(f"[red]Erreur : Port {port} déjà utilisé par '{app_using}'[/red]")
                return
            assigned_port = port
        else:
            # Attribution automatique
            assigned_port = registry.get_next_available_port(category)
    except ValueError as e:
        console.print(f"[red]Erreur : {e}[/red]")
        return
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")
        return

    # Vérifier si le port est utilisé par Docker
    if scanner.is_available() and scanner.is_port_in_use(assigned_port):
        container = scanner.get_container_by_port(assigned_port)
        console.print(f"[yellow]⚠ Attention : Port {assigned_port} déjà utilisé par le conteneur '{container}'[/yellow]")

    # Enregistrer
    registry.add(name, assigned_port, category)

    console.print(f"[green]✓ Port {assigned_port} attribué à \"{name}\"[/green]")
    if category:
        console.print(f"  Catégorie : {category}")
    console.print(f"\n  Utilise dans ton docker-compose.yml :")
    console.print(f"  [cyan]ports:[/cyan]")
    console.print(f"  [cyan]  - \"{assigned_port}:3000\"[/cyan]")


@main.command('list')
@click.option('--category', '-c', default=None, help="Filtrer par catégorie")
def list_apps(category):
    """Liste toutes les apps et leurs ports"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    registry = Registry()
    scanner = DockerScanner()
    apps = registry.get_all()

    if not apps:
        console.print("[yellow]Aucune app enregistrée.[/yellow]")
        return

    # Filtrer par catégorie si spécifié
    if category:
        apps = {k: v for k, v in apps.items() if v.get('category') == category}
        if not apps:
            console.print(f"[yellow]Aucune app dans la catégorie '{category}'[/yellow]")
            return

    # Créer le tableau
    table = Table(title="Apps enregistrées")
    table.add_column("App", style="cyan")
    table.add_column("Port", style="green")
    table.add_column("Catégorie", style="yellow")
    table.add_column("Actif", style="magenta")

    for name, app in sorted(apps.items(), key=lambda x: x[1]['port']):
        is_active = "✓" if scanner.is_port_in_use(app['port']) else "-"
        cat = app.get('category') or '-'
        table.add_row(name, str(app['port']), cat, is_active)

    console.print(table)

    # Résumé
    ports_list = [str(app['port']) for app in apps.values()]
    console.print(f"\n{len(apps)} apps · Ports : {', '.join(sorted(ports_list, key=int))}")


@main.command()
@click.argument('port', type=int)
def check(port):
    """Vérifie si un port est disponible"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    registry = Registry()
    scanner = DockerScanner()

    # Vérifier dans le registre
    app_name = registry.get_app_by_port(port)
    if app_name:
        console.print(f"[red]✗ Port {port} est utilisé par \"{app_name}\"[/red]")
        return

    # Vérifier dans Docker
    if scanner.is_available() and scanner.is_port_in_use(port):
        container = scanner.get_container_by_port(port)
        console.print(f"[yellow]⚠ Port {port} utilisé par le conteneur '{container}' (non enregistré dans portier)[/yellow]")
        return

    console.print(f"[green]✓ Port {port} est disponible[/green]")


@main.command()
@click.argument('name')
def remove(name):
    """Supprime une app et libère son port"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    registry = Registry()
    apps = registry.get_all()

    if name not in apps:
        console.print(f"[red]Erreur : App '{name}' introuvable[/red]")
        return

    port = apps[name]['port']
    registry.remove(name)
    console.print(f"[green]✓ Port {port} libéré (app \"{name}\" supprimée)[/green]")


@main.command()
def sync():
    """Synchronise le registre avec Docker"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    registry = Registry()
    scanner = DockerScanner()

    if not scanner.is_available():
        console.print("[red]Erreur : Docker n'est pas accessible[/red]")
        return

    apps = registry.get_all()
    containers = scanner.get_running_containers()
    container_ports = {c['host_port']: c['name'] for c in containers}

    changes = False

    # Vérifier les apps orphelines (dans le registre mais pas dans Docker)
    for name, app in list(apps.items()):
        port = app['port']
        if port not in container_ports:
            console.print(f"[yellow]⚠ \"{name}\" (port {port}) : conteneur introuvable[/yellow]")
            if click.confirm("  Libérer ce port ?"):
                registry.remove(name)
                console.print(f"  [green]✓ Port {port} libéré[/green]")
                changes = True

    # Vérifier les conteneurs non enregistrés
    registered_ports = registry.get_used_ports()
    for port, container_name in container_ports.items():
        if port not in registered_ports:
            console.print(f"[yellow]⚠ Conteneur '{container_name}' sur port {port} (non enregistré)[/yellow]")
            if click.confirm("  Ajouter au registre ?"):
                registry.add(container_name, port)
                console.print(f"  [green]✓ \"{container_name}\" ajouté (port {port})[/green]")
                changes = True

    if not changes:
        console.print("[green]✓ Tout est synchronisé[/green]")


@main.command()
def scan():
    """Scanne les conteneurs Docker existants"""
    scanner = DockerScanner()

    if not scanner.is_available():
        console.print("[red]Erreur : Docker n'est pas accessible[/red]")
        return

    containers = scanner.get_running_containers()

    if not containers:
        console.print("[yellow]Aucun conteneur avec des ports exposés[/yellow]")
        return

    table = Table(title="Conteneurs Docker détectés")
    table.add_column("Conteneur", style="cyan")
    table.add_column("Port hôte", style="green")
    table.add_column("Port conteneur", style="yellow")

    for c in sorted(containers, key=lambda x: x['host_port']):
        table.add_row(c['name'], str(c['host_port']), c['container_port'])

    console.print(table)


@main.command()
def categories():
    """Liste les catégories configurées"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    config = Config()
    cats = config.list_categories()

    if not cats:
        console.print("[yellow]Aucune catégorie configurée.[/yellow]")
        console.print("Utilise 'portier config add-category' pour en ajouter.")
        return

    table = Table(title="Catégories")
    table.add_column("Nom", style="cyan")
    table.add_column("Plage", style="green")
    table.add_column("Description", style="yellow")

    for name, cat in cats.items():
        range_str = f"{cat['range'][0]}-{cat['range'][1]}"
        desc = cat.get('description') or '-'
        table.add_row(name, range_str, desc)

    console.print(table)


@main.group()
def config():
    """Gère la configuration de portier"""
    pass


@config.command('add-category')
@click.argument('name')
@click.option('--range', 'range_str', required=True, help="Plage de ports (ex: 3000-3099)")
@click.option('--description', '-d', default=None, help="Description de la catégorie")
def add_category(name, range_str, description):
    """Ajoute une nouvelle catégorie"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    # Parser la plage
    try:
        start, end = map(int, range_str.split('-'))
    except ValueError:
        console.print("[red]Erreur : Format de plage invalide. Utilise 'start-end' (ex: 3000-3099)[/red]")
        return

    cfg = Config()
    cfg.add_category(name, start, end, description)
    console.print(f"[green]✓ Catégorie \"{name}\" ajoutée ({start}-{end})[/green]")


@config.command('remove-category')
@click.argument('name')
def remove_category(name):
    """Supprime une catégorie"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    cfg = Config()
    if cfg.remove_category(name):
        console.print(f"[green]✓ Catégorie \"{name}\" supprimée[/green]")
    else:
        console.print(f"[red]Erreur : Catégorie '{name}' introuvable[/red]")

@config.command('set-range')
@click.option('--start', required=True, type=int, help="Port de début de la plage")
@click.option('--end', required=True, type=int, help="Port de fin de la plage")
def set_range(start, end):
    """Modifie la plage de ports par défaut"""
    if not is_initialized():
        console.print("[red]Erreur : Portier n'est pas initialisé. Lance 'portier init' d'abord.[/red]")
        return

    if start >= end:
        console.print("[red]Erreur : Le port de début doit être inférieur au port de fin[/red]")
        return

    if start < 1 or end > 65535:
        console.print("[red]Erreur : Les ports doivent être entre 1 et 65535[/red]")
        return

    cfg = Config()
    cfg.set_range(start, end)
    console.print(f"[green]✓ Plage de ports mise à jour : {start}-{end}[/green]")

if __name__ == '__main__':
    main()