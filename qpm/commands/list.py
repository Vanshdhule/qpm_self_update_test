# QVoid-MutantAI/qpm/commands/list.py
import os
import json
import click

# Define the installation directory (same as in install.py)
QPM_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_PACKAGES_DIR = os.path.abspath(os.path.join(QPM_ROOT_DIR, '..', 'packages'))

def list_packages():
    """
    Lists all currently installed QVoid packages.
    """
    click.echo("\n🔍 Currently Installed QVoid Packages:")
    click.echo("-------------------------------------")

    if not os.path.exists(INSTALL_PACKAGES_DIR) or not os.listdir(INSTALL_PACKAGES_DIR):
        click.echo("No packages installed yet.")
        click.echo("-------------------------------------")
        return

    found_packages = False
    for package_name_dir in os.listdir(INSTALL_PACKAGES_DIR):
        package_base_path = os.path.join(INSTALL_PACKAGES_DIR, package_name_dir)
        if os.path.isdir(package_base_path):
            # Iterate through version subdirectories
            for version_dir in os.listdir(package_base_path):
                package_version_path = os.path.join(package_base_path, version_dir)
                if os.path.isdir(package_version_path):
                    manifest_path = os.path.join(package_version_path, "qvoid_package.json")
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                                name = manifest.get("name", package_name_dir) # Use dir name as fallback
                                version = manifest.get("version", version_dir) # Use dir name as fallback
                                description = manifest.get("description", "No description provided.")
                                click.echo(f"📦 {name} (v{version})")
                                click.echo(f"   Description: {description}")
                                click.echo(f"   Installed at: {package_version_path}")
                                click.echo("") # Empty line for readability
                                found_packages = True
                        except json.JSONDecodeError:
                            click.echo(f"⚠️ Corrupted manifest for package in {package_version_path}")
                        except Exception as e:
                            click.echo(f"❌ Error reading manifest for {package_version_path}: {e}")

    if not found_packages:
        click.echo("No valid packages found in installation directory.")
    click.echo("-------------------------------------")