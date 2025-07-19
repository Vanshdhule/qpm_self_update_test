# QVoid-MutantAI/qpm/utils/integrity.py
import hashlib
import click

def calculate_checksum(file_path, algorithm='sha256'):
    """Calculates the SHA256 checksum of a file."""
    hash_algo = hashlib.sha256() # Default to SHA256
    if algorithm == 'md5':
        hash_algo = hashlib.md5()
    elif algorithm == 'sha1':
        hash_algo = hashlib.sha1()
    elif algorithm == 'sha256':
        hash_algo = hashlib.sha256()
    elif algorithm == 'sha512':
        hash_algo = hashlib.sha512()
    else:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_algo.update(chunk)
    return hash_algo.hexdigest()

def verify_checksum(file_path, expected_checksum, algorithm='sha256'):
    """Verifies the checksum of a file against an expected checksum."""
    actual_checksum = calculate_checksum(file_path, algorithm)
    if actual_checksum == expected_checksum:
        click.echo(f"✅ Checksum verification successful ({algorithm}).")
        return True
    else:
        click.echo(f"❌ Checksum mismatch ({algorithm})!")
        click.echo(f"   Expected: {expected_checksum}")
        click.echo(f"   Actual:   {actual_checksum}")
        return False