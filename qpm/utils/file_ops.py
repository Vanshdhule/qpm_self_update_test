# QVoid-MutantAI/qpm/utils/file_ops.py
import os
import requests
import zipfile
import shutil
import click # For consistent output using click.echo

def download_file(url, destination_path):
    """Downloads a file from a URL to a specified path."""
    click.echo(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            with open(destination_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        click.echo(f"Downloaded to {destination_path}")
        return True
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Network or download error: {e}")
        return False
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred during download: {e}")
        return False

def extract_zip(zip_path, destination_dir):
    """Extracts a zip archive to a specified directory."""
    click.echo(f"Extracting {zip_path} to {destination_dir}...")
    try:
        # Ensure the destination directory exists
        os.makedirs(destination_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)
        click.echo("Extraction complete.")
        return True
    except zipfile.BadZipFile:
        click.echo(f"❌ Error: {zip_path} is not a valid zip file.")
        return False
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred during extraction: {e}")
        return False

def clean_up_temp_file(file_path):
    """Removes a temporary file."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            click.echo(f"Cleaned up temporary file: {file_path}")
        except OSError as e:
            click.echo(f"⚠️ Warning: Could not remove temporary file {file_path}: {e}")

def remove_directory(path):
    """Removes a directory and its contents."""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            click.echo(f"Removed directory: {path}")
        except OSError as e:
            click.echo(f"❌ Error removing directory {path}: {e}")
            return False
    return True