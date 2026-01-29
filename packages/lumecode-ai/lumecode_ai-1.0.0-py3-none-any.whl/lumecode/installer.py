"""
Binary installer for Lumecode CLI tool.
Downloads and manages the Go binary from GitHub releases.
"""

import os
import sys
import stat
import tarfile
import zipfile
import platform
import tempfile
import shutil
from pathlib import Path

import requests
from platformdirs import user_data_dir

VERSION = "1.0.0"
GITHUB_RELEASE_URL = "https://github.com/anonymus-netizien/lumecode/releases/download/v{version}"

CHECKSUMS = {
    "darwin-amd64": "8fa33c920f6e095e79534a0971393e3557cda86128e2c7937684bf9515b0345e",
    "darwin-arm64": "441d22f0568eb78079112a53a4cfecff8cb73932ede2c9bcb5243ccd242f4e1b",
    "linux-amd64": "fc092426a22a44434328dbb9d799aebe129e662b6d35c6d04e17b61670c315d0",
    "linux-arm64": "a3d8971d06ae4e8e10debf08bc767f94dfb2fdb861454c725aa5d36e6c76d2a5",
    "windows-amd64": "bc75288d0a7ae4dc7d27c5c71357984b0a30608ad8484ac29652bdf29ba8fc92",
}


def get_platform_info():
    """Detect the current platform and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Normalize OS name
    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    elif system == "windows":
        os_name = "windows"
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")
    
    # Normalize architecture
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")
    
    return os_name, arch


def get_install_dir():
    """Get the installation directory for the binary."""
    return Path(user_data_dir("lumecode", "lumecode")) / "bin"


def get_binary_path():
    """Get the full path to the lumecode binary."""
    install_dir = get_install_dir()
    os_name, _ = get_platform_info()
    
    if os_name == "windows":
        return install_dir / "lumecode.exe"
    return install_dir / "lumecode"


def download_binary(version=VERSION):
    """Download the lumecode binary for the current platform."""
    os_name, arch = get_platform_info()
    platform_key = f"{os_name}-{arch}"
    
    if platform_key not in CHECKSUMS:
        raise RuntimeError(f"No binary available for {platform_key}")
    
    # Determine archive extension
    if os_name == "windows":
        ext = "zip"
        archive_name = f"lumecode-v{version}-{platform_key}.zip"
    else:
        ext = "tar.gz"
        archive_name = f"lumecode-v{version}-{platform_key}.tar.gz"
    
    url = f"{GITHUB_RELEASE_URL.format(version=version)}/{archive_name}"
    
    print(f"Downloading lumecode v{version} for {platform_key}...")
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = (downloaded / total) * 100
                print(f"\rProgress: {pct:.1f}%", end="", flush=True)
        
        print()
        return tmp.name, os_name, platform_key


def extract_binary(archive_path, os_name, platform_key):
    """Extract the binary from the archive."""
    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)
    
    if os_name == "windows":
        binary_name = f"lumecode-{platform_key}.exe"
        target_name = "lumecode.exe"
        
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Find the binary in the archive
            for name in zf.namelist():
                if name.endswith('.exe'):
                    with zf.open(name) as src:
                        target = install_dir / target_name
                        with open(target, 'wb') as dst:
                            dst.write(src.read())
                    break
    else:
        binary_name = f"lumecode-{platform_key}"
        target_name = "lumecode"
        
        with tarfile.open(archive_path, 'r:gz') as tf:
            for member in tf.getmembers():
                if member.name == binary_name:
                    member.name = target_name
                    tf.extract(member, install_dir)
                    break
    
    # Make executable
    binary_path = install_dir / target_name
    if os_name != "windows":
        binary_path.chmod(binary_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    # Cleanup
    os.unlink(archive_path)
    
    return binary_path


def install(version=VERSION, force=False):
    """Install or update the lumecode binary."""
    binary_path = get_binary_path()
    
    if binary_path.exists() and not force:
        print(f"Lumecode already installed at {binary_path}")
        print("Use force=True to reinstall")
        return binary_path
    
    try:
        archive_path, os_name, platform_key = download_binary(version)
        binary_path = extract_binary(archive_path, os_name, platform_key)
        print(f"✓ Installed lumecode to {binary_path}")
        return binary_path
    except Exception as e:
        print(f"✗ Installation failed: {e}")
        raise


def uninstall():
    """Remove the lumecode binary."""
    binary_path = get_binary_path()
    install_dir = get_install_dir()
    
    if binary_path.exists():
        binary_path.unlink()
        print(f"✓ Removed {binary_path}")
    
    # Try to remove the directory if empty
    try:
        install_dir.rmdir()
        print(f"✓ Removed {install_dir}")
    except OSError:
        pass  # Directory not empty or doesn't exist


def ensure_installed():
    """Ensure lumecode is installed, install if not."""
    binary_path = get_binary_path()
    if not binary_path.exists():
        return install()
    return binary_path
