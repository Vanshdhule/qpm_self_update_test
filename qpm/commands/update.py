# QVoid-MutantAI/qpm/commands/update.py
import os
import json
import requests
from packaging.version import parse as parse_version # For robust version comparison
import click

# Define the installation directory (same as in install.py)
QPM_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_PACKAGES_DIR = os.path.abspath(os.path.join(QPM_ROOT_DIR, '..', 'packages'))

def fetch_remote_manifest(source_url):
    """
    Fetches and parses a qvoid_package.json manifest from a remote URL.
    Assumes the manifest is directly accessible at the source_url,
    or within a zip file that can be downloaded and inspected.
    For this step, we're assuming the manifest itself might be accessible or
    we're getting it from the *same* zip URL as the install.
    A more advanced update system would have a dedicated manifest endpoint.
    """
    click.echo(f"Fetching remote manifest from: {source_url}")
    try:
        # For simplicity in this step, let's assume the source_url points directly to a manifest
        # OR we will extract it from the downloaded zip if it's a zip URL.
        # Given your install is from a zip, we'll simulate getting the manifest from the zip structure.
        # In a real update system, you'd likely have a separate manifest server.

        # Simulate fetching the manifest from a hypothetical location
        # For now, we'll assume source_url refers to the zip, and we need to derive manifest URL
        # This is a simplification. A real registry would provide manifest.
        # Let's adjust this to actually download the zip and read its manifest again.

        # This part needs to be careful: We need to download the *latest* zip,
        # extract its manifest, and then remove the temp zip.

        import tempfile
        from ..utils import file_ops # Import file_ops

        temp_dir = tempfile.mkdtemp(prefix="qpm_update_manifest_")
        temp_zip_path = os.path.join(temp_dir, "latest_package.zip")
        manifest = None

        try:
            if not file_ops.download_file(source_url, temp_zip_path):
                raise Exception("Failed to download latest package for manifest check.")

            extracted_content_root_path = os.path.join(temp_dir, "extracted_content_root")
            if not file_ops.extract_zip(temp_zip_path, extracted_content_root_path):
                raise Exception("Failed to extract latest package for manifest check.")

            package_manifest_parent_dir = extracted_content_root_path
            potential_root_dirs = [d for d in os.listdir(extracted_content_root_path) if os.path.isdir(os.path.join(extracted_content_root_path, d))]

            if len(potential_root_dirs) == 1:
                package_manifest_parent_dir = os.path.join(extracted_content_root_path, potential_root_dirs[0])

            manifest_path = os.path.join(package_manifest_parent_dir, "qvoid_package.json")

            if not os.path.exists(manifest_path):
                raise Exception("qvoid_package.json manifest not found in the remote package.")

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

        finally:
            if temp_dir and os.path.exists(temp_dir):
                file_ops.remove_directory(temp_dir)

        return manifest

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Network error fetching remote manifest: {e}")
        return None
    except json.JSONDecodeError:
        click.echo(f"❌ Error parsing remote manifest from {source_url}: Invalid JSON.")
        return None
    except Exception as e:
        click.echo(f"❌ Error fetching remote manifest: {e}")
        return None

def check_for_updates(package_name=None):
    """
    Checks for updates for a specific package or all installed packages.
    """
    click.echo("\n🔄 Checking for package updates...")
    click.echo("-------------------------------------")

    installed_packages = {}
    # Re-read installed packages by iterating through our packages directory
    QPM_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTALL_PACKAGES_DIR = os.path.abspath(os.path.join(QPM_ROOT_DIR, '..', 'packages'))

    if not os.path.exists(INSTALL_PACKAGES_DIR):
        click.echo("No packages directory found.")
        return

    for pkg_base_name in os.listdir(INSTALL_PACKAGES_DIR):
        pkg_base_path = os.path.join(INSTALL_PACKAGES_DIR, pkg_base_name)
        if os.path.isdir(pkg_base_path):
            for version_dir in os.listdir(pkg_base_path):
                pkg_version_path = os.path.join(pkg_base_path, version_dir)
                if os.path.isdir(pkg_version_path):
                    manifest_path = os.path.join(pkg_version_path, "qvoid_package.json")
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                                # Store the manifest for the installed package
                                installed_packages[manifest['name']] = {
                                    'version': manifest['version'],
                                    'source_url': manifest.get('source_url'),
                                    'path': pkg_version_path
                                }
                        except json.JSONDecodeError:
                            click.echo(f"⚠️ Corrupted manifest for package in {pkg_version_path}")
                        except Exception as e:
                            click.echo(f"❌ Error reading manifest for {pkg_version_path}: {e}")

    if not installed_packages:
        click.echo("No packages installed to check for updates.")
        click.echo("-------------------------------------")
        return

    packages_to_check = {}
    if package_name:
        if package_name in installed_packages:
            packages_to_check[package_name] = installed_packages[package_name]
        else:
            click.echo(f"❌ Package '{package_name}' is not installed.")
            click.echo("-------------------------------------")
            return
    else:
        packages_to_check = installed_packages

    updates_found = False
    for pkg_name, pkg_info in packages_to_check.items():
        current_version = pkg_info['version']
        source_url = pkg_info['source_url']

        if not source_url:
            click.echo(f"⚠️ Cannot check update for '{pkg_name}': No source_url specified in its manifest.")
            continue

        click.echo(f"\nChecking '{pkg_name}' (Current: v{current_version})...")
        remote_manifest = fetch_remote_manifest(source_url)

        if remote_manifest:
            remote_version_str = remote_manifest.get('version')
            if not remote_version_str:
                click.echo(f"⚠️ Remote manifest for '{pkg_name}' has no version. Cannot compare.")
                continue

            try:
                current_v = parse_version(current_version)
                remote_v = parse_version(remote_version_str)

                if remote_v > current_v:
                    click.echo(f"✨ Update available for '{pkg_name}': v{current_version} -> v{remote_version_str}")
                    updates_found = True
                else:
                    click.echo(f"✅ '{pkg_name}' is up to date (v{current_version}).")
            except Exception as e:
                click.echo(f"❌ Error comparing versions for '{pkg_name}': {e}. Current: '{current_version}', Remote: '{remote_version_str}'")
        else:
            click.echo(f"⚠️ Could not fetch remote manifest for '{pkg_name}'.")

    if not updates_found and not package_name: # Only if checking all and no specific package was requested
        click.echo("\nAll installed packages are up to date.")
    click.echo("-------------------------------------")