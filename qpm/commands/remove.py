# QVoid-MutantAI/qpm/commands/remove.py
import os
import click
from ..utils import file_ops # Re-use remove_directory

# Define the installation directory (same as in install.py)
QPM_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_PACKAGES_DIR = os.path.abspath(os.path.join(QPM_ROOT_DIR, '..', 'packages'))

def remove_package(package_name, version=None):
    """
    Removes an installed QVoid package.
    If version is None, it prompts to remove all versions.
    """
    click.echo(f"Initiating removal of package: {package_name}")

    package_base_path = os.path.join(INSTALL_PACKAGES_DIR, package_name)

    if not os.path.exists(package_base_path):
        click.echo(f"❌ Package '{package_name}' not found at {package_base_path}.")
        return False

    versions_found = []
    if os.path.isdir(package_base_path): # Ensure it's a directory
        for v_dir in os.listdir(package_base_path):
            if os.path.isdir(os.path.join(package_base_path, v_dir)):
                versions_found.append(v_dir)
    versions_found.sort() # Sort for consistent display

    if not versions_found:
        click.echo(f"❌ No installed versions found for package '{package_name}'.")
        return False

    target_paths_to_remove = []

    if version:
        if version not in versions_found:
            click.echo(f"❌ Version '{version}' of package '{package_name}' not found. Available versions: {', '.join(versions_found)}")
            return False
        target_paths_to_remove.append(os.path.join(package_base_path, version))
        confirmation_msg = f"Are you sure you want to remove package '{package_name}' v{version}?"
    else:
        click.echo(f"Found multiple versions for '{package_name}': {', '.join(versions_found)}")
        prompt_msg = f"Which version of '{package_name}' do you want to remove? (type 'all' for all, or 'cancel'): "
        selected_version = click.prompt(prompt_msg).strip().lower()

        if selected_version == 'cancel':
            click.echo("Removal cancelled.")
            return False
        elif selected_version == 'all':
            for v_dir in versions_found:
                target_paths_to_remove.append(os.path.join(package_base_path, v_dir))
            confirmation_msg = f"Are you sure you want to remove ALL versions of package '{package_name}'?"
        elif selected_version in versions_found:
            target_paths_to_remove.append(os.path.join(package_base_path, selected_version))
            confirmation_msg = f"Are you sure you want to remove package '{package_name}' v{selected_version}?"
        else:
            click.echo("❌ Invalid version specified.")
            return False

    if not click.confirm(confirmation_msg):
        click.echo("Removal cancelled by user.")
        return False

    all_removed_successfully = True
    for path_to_remove in target_paths_to_remove:
        click.echo(f"Removing: {path_to_remove}")
        if not file_ops.remove_directory(path_to_remove):
            all_removed_successfully = False
            click.echo(f"❌ Failed to remove {path_to_remove}.")

    # After removing version(s), check if the base package_name_dir is now empty
    if all_removed_successfully and os.path.exists(package_base_path) and not os.listdir(package_base_path):
        click.echo(f"Base directory for '{package_name}' is now empty. Removing it...")
        file_ops.remove_directory(package_base_path)

    if all_removed_successfully:
        click.echo(f"✅ Package '{package_name}' removed successfully.")
        return True
    else:
        click.echo(f"⚠️ Some parts of package '{package_name}' could not be removed.")
        return False