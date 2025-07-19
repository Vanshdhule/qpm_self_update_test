# QVoid-MutantAI/qpm/commands/install.py
import os
import tempfile
import json
import shutil
import click
from ..utils import file_ops
from ..utils import integrity
from ..utils import sandbox

# Define the base directory for QPM within the project
QPM_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_PACKAGES_DIR = os.path.abspath(os.path.join(QPM_ROOT_DIR, '..', 'packages'))
os.makedirs(INSTALL_PACKAGES_DIR, exist_ok=True)

# A simple cache for installed packages to avoid redundant checks and help with dependencies
# In a real system, this would be more persistent and robust.
_INSTALLED_PACKAGES_CACHE = {}

def _refresh_installed_packages_cache():
    """Refreshes the internal cache of installed packages."""
    global _INSTALLED_PACKAGES_CACHE
    _INSTALLED_PACKAGES_CACHE = {}
    if not os.path.exists(INSTALL_PACKAGES_DIR):
        return

    for package_name_dir in os.listdir(INSTALL_PACKAGES_DIR):
        package_base_path = os.path.join(INSTALL_PACKAGES_DIR, package_name_dir)
        if os.path.isdir(package_base_path):
            for version_dir in os.listdir(package_base_path):
                package_version_path = os.path.join(package_base_path, version_dir)
                if os.path.isdir(package_version_path):
                    manifest_path = os.path.join(package_version_path, "qvoid_package.json")
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                                name = manifest.get("name")
                                version = manifest.get("version")
                                if name and version:
                                    if name not in _INSTALLED_PACKAGES_CACHE:
                                        _INSTALLED_PACKAGES_CACHE[name] = {}
                                    _INSTALLED_PACKAGES_CACHE[name][version] = {
                                        'path': package_version_path,
                                        'source_url': manifest.get('source_url'),
                                        'checksum': manifest.get('checksum')
                                    }
                        except json.JSONDecodeError:
                            click.echo(f"⚠️ Corrupted manifest for package in {package_version_path}", err=True)
                        except Exception as e:
                            click.echo(f"❌ Error refreshing cache for {package_version_path}: {e}", err=True)

# Initial cache refresh
_refresh_installed_packages_cache()


def is_package_installed(package_name, version=None):
    """Checks if a package (and optionally a specific version) is installed."""
    _refresh_installed_packages_cache() # Always fresh check for critical operations
    if package_name in _INSTALLED_PACKAGES_CACHE:
        if version:
            return version in _INSTALLED_PACKAGES_CACHE[package_name]
        return True # Any version is installed
    return False

# Keep track of packages currently in the process of being installed to prevent cycles
_INSTALLING_STACK = []

def install_package(source_url):
    """
    Installs a package from a given URL (assumed to be a zip file).
    Reads manifest, performs checksum verification, runs install script,
    and handles basic dependencies.
    """
    # Check for recursive calls for dependency handling
    if source_url in _INSTALLING_STACK:
        click.echo(f"⚠️ Circular dependency detected or package already on stack for installation: {source_url}. Skipping recursive install.")
        return True # Treat as successful for the current recursive call

    _INSTALLING_STACK.append(source_url) # Add to stack

    temp_dir = None
    temp_zip_path = None
    extracted_content_root_path = None
    package_name_from_manifest = "unknown_package"
    package_version = "0.0.0"
    final_package_version_dir = None

    try:
        click.echo(f"\n📦 Attempting to install {source_url}")

        temp_dir = tempfile.mkdtemp(prefix="qpm_install_")
        temp_zip_path = os.path.join(temp_dir, "package.zip")

        if not file_ops.download_file(source_url, temp_zip_path):
            raise Exception("Failed to download package.")

        extracted_content_root_path = os.path.join(temp_dir, "extracted_content_root")
        if not file_ops.extract_zip(temp_zip_path, extracted_content_root_path):
            raise Exception("Failed to extract package.")

        # Determine the actual package root within the extracted content
        package_manifest_parent_dir = extracted_content_root_path
        potential_root_dirs = [d for d in os.listdir(extracted_content_root_path) if os.path.isdir(os.path.join(extracted_content_root_path, d))]

        if len(potential_root_dirs) == 1:
            package_manifest_parent_dir = os.path.join(extracted_content_root_path, potential_root_dirs[0])
            click.echo(f"Identified potential package root within zip: {os.path.basename(package_manifest_parent_dir)}")

        manifest_path = os.path.join(package_manifest_parent_dir, "qvoid_package.json")

        if not os.path.exists(manifest_path):
            raise Exception("qvoid_package.json manifest not found in the extracted package.")

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        package_name_from_manifest = manifest.get("name")
        package_version = manifest.get("version")
        expected_checksum = manifest.get("checksum")
        dependencies = manifest.get("dependencies", []) # Get dependencies

        if not package_name_from_manifest or not package_version or not expected_checksum:
            raise Exception("Manifest is missing required 'name', 'version', or 'checksum' fields.")

        click.echo(f"Manifest loaded: {package_name_from_manifest} v{package_version}")
        click.echo(f"Expected checksum from manifest: {expected_checksum}")

        # Check if package is already installed (and is the same version)
        if is_package_installed(package_name_from_manifest, package_version):
            click.echo(f"✅ Package '{package_name_from_manifest} v{package_version}' is already installed. Skipping.")
            return True

        if not integrity.verify_checksum(temp_zip_path, expected_checksum):
            raise Exception("Checksum verification failed. Package might be corrupted or tampered with.")

        # --- Dependency Resolution (NEW) ---
        if dependencies:
            click.echo(f"Dependency check for {package_name_from_manifest}...")
            for dep_name in dependencies:
                # For basic dependency, we assume the dependency name is enough.
                # In a real system, you might need a registry to find its source_url.
                # For this exercise, we'll assume dependent packages also need to be installed via `qpm install <URL>`
                # and that their URLs are hardcoded or available from a simple registry.
                # For a simple test, ensure your dependency is installed manually or has a known URL.

                # Here, we'll just check if it's installed. If not, this is where
                # a recursive install call or a lookup in a central registry would happen.
                if not is_package_installed(dep_name):
                    click.echo(f"Dependent package '{dep_name}' not found. Please install it first or ensure it's in a registry.")
                    # For a robust system, you'd try to install it here:
                    # if not install_package(<dep_source_url>): # Requires lookup
                    #    raise Exception(f"Failed to install dependency: {dep_name}")
                    raise Exception(f"Missing dependency: {dep_name}. Please install it manually.")
                else:
                    click.echo(f"Dependent package '{dep_name}' is installed.")
        # --- End Dependency Resolution ---

        final_package_base_dir = os.path.join(INSTALL_PACKAGES_DIR, package_name_from_manifest)
        final_package_version_dir = os.path.join(final_package_base_dir, package_version)

        if os.path.exists(final_package_version_dir):
            click.echo(f"Existing package version '{package_name_from_manifest} v{package_version}' found. Overwriting...")
            file_ops.remove_directory(final_package_version_dir)

        os.makedirs(final_package_base_dir, exist_ok=True)
        shutil.move(package_manifest_parent_dir, final_package_version_dir)
        click.echo(f"✅ Package '{package_name_from_manifest} v{package_version}' installed successfully to: {final_package_version_dir}")

        install_script_path_relative = manifest.get("install_script")
        if install_script_path_relative:
            full_script_path = os.path.join(final_package_version_dir, install_script_path_relative)
            if os.path.exists(full_script_path):
                click.echo(f"Running install script '{install_script_path_relative}'...")
                if not sandbox.run_script_in_virtualenv(full_script_path, cwd=final_package_version_dir):
                    raise Exception("Install script execution failed in sandbox.")
            else:
                click.echo(f"⚠️ Warning: Install script '{install_script_path_relative}' specified but not found at {full_script_path}.")

        _refresh_installed_packages_cache() # Refresh cache after successful install

    except Exception as e:
        click.echo(f"❌ Error during installation of {package_name_from_manifest}: {e}", err=True)
        if final_package_version_dir and os.path.exists(final_package_version_dir):
            click.echo(f"Attempting to clean up partial installation at {final_package_version_dir}...", err=True)
            file_ops.remove_directory(final_package_version_dir)

        click.echo("Installation failed. Cleaned up temporary files.", err=True)
        return False
    finally:
        if temp_dir and os.path.exists(temp_dir):
            file_ops.remove_directory(temp_dir)
        # Remove from stack regardless of success/failure
        if _INSTALLING_STACK and _INSTALLING_STACK[-1] == source_url:
            _INSTALLING_STACK.pop()
    return True