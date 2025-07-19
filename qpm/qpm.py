# qpm/qpm.py

import click
from .commands.install import install_package
from .commands.list import list_packages
from .commands.remove import remove_package
from .commands.update import check_for_updates
from .commands.self_update import self_update_qpm

@click.group()
def cli():
    """
    QVoid Package Manager (qpm)

    A simple and secure command-line tool to easily install, update, and manage all
    the native tools and plugins within the Q-Void ecosystem.
    """
    pass

@cli.command()
def hello():
    """Says hello from qpm!"""
    click.echo("Hello from qpm!")

@cli.command()
@click.argument('source')
def install(source):
    """
    Installs a QVoid package from a given source (URL to a .zip file).
    Example: qpm install https://example.com/my_package.zip
    """
    click.echo(f"Attempting to install from: {source}")
    install_package(source)

@cli.command()
def list():
    """Lists all currently installed QVoid packages."""
    list_packages()

@cli.command()
@click.argument('package_name', required=False)
def update(package_name):
    """
    Checks for updates for a specific QVoid package or all installed packages.
    Example: qpm update                           (checks all)
    Example: qpm update test-package-one          (checks specific)
    """
    check_for_updates(package_name)

@cli.command('self-update')
def self_update():
    """Checks for and installs updates for QPM itself."""
    self_update_qpm()

@cli.command()
@click.argument('package_name')
@click.option('--version', '-v', help='Specific version to remove. If not provided, will prompt if multiple versions exist.')
def remove(package_name, version):
    """
    Removes an installed QVoid package.
    Example: qpm remove test-package-one
    Example: qpm remove test-package-one -v 1.0.0
    """
    remove_package(package_name, version)

if __name__ == '__main__':
    cli()
