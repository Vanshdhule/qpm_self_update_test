# qpm/commands/self_update.py

import os
import json
import requests
import tempfile
import shutil
import subprocess
import sys
from packaging.version import parse as parse_version
import click

from ..utils import file_ops  # For download and extraction
from ..utils import integrity  # For checksum verification

QPM_MANIFEST_URL = "https://raw.githubusercontent.com/Vanshdhule/qpm_self_update_test/main/qvoid_package_qpm.json"
QPM_INSTALL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _get_current_qpm_version():
    manifest_path = os.path.join(QPM_INSTALL_ROOT, "qvoid_package.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                return manifest.get("version", "0.0.0")
        except (json.JSONDecodeError, KeyError):
            click.echo("⚠️ Could not read current QPM version from its manifest. Assuming 0.0.0", err=True)
            return "0.0.0"
    return "0.0.0"

def self_update_qpm():
    click.echo("\n🚀 Checking for QPM updates...")
    current_version = _get_current_qpm_version()
    click.echo(f"Current QPM version: v{current_version}")

    temp_dir = None

    try:
        response = requests.get(QPM_MANIFEST_URL, timeout=10)
        response.raise_for_status()
        remote_qpm_manifest = response.json()

        remote_version_str = remote_qpm_manifest.get("version")
        remote_source_url = remote_qpm_manifest.get("source_url")
        remote_checksum = remote_qpm_manifest.get("checksum")
        qpm_package_name = remote_qpm_manifest.get("name", "qpm")

        if not remote_version_str or not remote_source_url or not remote_checksum:
            raise Exception("Remote QPM manifest is incomplete (missing version, source_url, or checksum).")

        click.echo(f"Latest QPM version available: v{remote_version_str}")

        current_v = parse_version(current_version)
        remote_v = parse_version(remote_version_str)

        if remote_v <= current_v:
            click.echo("✅ QPM is already up to date.")
            return True

        click.echo(f"✨ New QPM version v{remote_version_str} available! Starting update...")

        temp_dir = tempfile.mkdtemp(prefix="qpm_self_update_")
        temp_zip_path = os.path.join(temp_dir, f"{qpm_package_name}-{remote_version_str}.zip")

        if not file_ops.download_file(remote_source_url, temp_zip_path):
            raise Exception("Failed to download new QPM version.")

        if not integrity.verify_checksum(temp_zip_path, remote_checksum):
            raise Exception("Checksum verification failed for new QPM version. Download might be corrupted.")

        extracted_qpm_root_path = os.path.join(temp_dir, "new_qpm_extracted")
        if not file_ops.extract_zip(temp_zip_path, extracted_qpm_root_path):
            raise Exception("Failed to extract new QPM version.")

        qpm_content_source_path = extracted_qpm_root_path
        extracted_subdirs = [d for d in os.listdir(extracted_qpm_root_path)
                             if os.path.isdir(os.path.join(extracted_qpm_root_path, d))]
        if len(extracted_subdirs) == 1:
            qpm_content_source_path = os.path.join(extracted_qpm_root_path, extracted_subdirs[0])

        if not os.path.exists(os.path.join(qpm_content_source_path, "qpm.py")) or \
           not os.path.exists(os.path.join(qpm_content_source_path, "commands")) or \
           not os.path.exists(os.path.join(qpm_content_source_path, "utils")):
            raise Exception("Extracted QPM content structure is invalid.")

        click.echo("Performing atomic update (requires external script/restart)...")

        updater_script_path = os.path.join(tempfile.gettempdir(), f"qpm_updater_{os.urandom(4).hex()}.py")

        current_qpm_script = os.path.abspath(sys.argv[0])

        updater_script_content = f"""
import os
import shutil
import sys
import time

old_qpm_root = "{QPM_INSTALL_ROOT.replace(os.sep, '/')}"
new_qpm_source = "{qpm_content_source_path.replace(os.sep, '/')}"
temp_updater_dir = "{temp_dir.replace(os.sep, '/')}"

time.sleep(1)

print("\\n[QPM Updater] Starting self-update...")

try:
    backup_dir = old_qpm_root + "_old_backup_" + str(int(time.time()))
    if os.path.exists(old_qpm_root):
        print(f"[QPM Updater] Backing up old QPM to: {{backup_dir}}")
        shutil.copytree(old_qpm_root, backup_dir)
        shutil.rmtree(old_qpm_root)

    print(f"[QPM Updater] Copying new QPM from {{new_qpm_source}} to {{old_qpm_root}}")
    shutil.copytree(new_qpm_source, old_qpm_root)
    print("[QPM Updater] QPM updated successfully!")

    if os.path.exists(temp_updater_dir):
        print(f"[QPM Updater] Cleaning up temporary directory: {{temp_updater_dir}}")
        shutil.rmtree(temp_updater_dir)

    print(f"[QPM Updater] You can remove {{backup_dir}} if everything works correctly.")
    print("[QPM Updater] Self-update finished.")
except Exception as e:
    print(f"[QPM Updater] ❌ Self-update failed: {{e}}", file=sys.stderr)
    print("[QPM Updater] You may need to manually restore from backup.", file=sys.stderr)
"""

        with open(updater_script_path, "w") as f:
            f.write(updater_script_content)

        click.echo(f"Updater script created at: {updater_script_path}")
        click.echo("QPM will now exit to apply the update. Please re-run QPM after a moment.")

        if sys.platform == "win32":
            subprocess.Popen(['start', '""', '/B', sys.executable, updater_script_path], shell=True)
        else:
            subprocess.Popen(['nohup', sys.executable, updater_script_path, '&'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)

        sys.exit(0)

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Network error during QPM self-update: {e}", err=True)
    except json.JSONDecodeError:
        click.echo(f"❌ Error parsing remote QPM manifest: Invalid JSON.", err=True)
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred during QPM self-update: {e}", err=True)
    finally:
        if temp_dir and os.path.exists(temp_dir):
            file_ops.remove_directory(temp_dir)

    return False
