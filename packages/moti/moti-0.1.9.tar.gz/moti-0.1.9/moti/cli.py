"""Moti CLI - runs run.py from current directory or code from MOTI_CODE_URL."""

import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
import urllib.request
import json


def load_and_set_config(config_json):
    """Parse JSON config and set all values as MOTI_ env variables."""
    
    try:
        config = json.loads(config_json)
    except Exception as e:
        print(f"✗ Failed to parse config: {e}")
        sys.exit(1)
    
    # Set each config value as MOTI_<KEY> environment variable
    for key, value in config.items():
        env_key = f"MOTI_{key.upper()}"
        env_value = str(value) if not isinstance(value, bool) else str(value).lower()
        os.environ[env_key] = env_value
    
    # Save config to /tmp/moti.json
    try:
        with open("/tmp/moti.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"✓ Config saved to /tmp/moti.json")
    except Exception as e:
        print(f"⚠ Failed to save config to /tmp/moti.json: {e}")
    
    print(f"✓ Config loaded, {len(config)} variables set")
    return config


def get_code_directory():
    """Get the code directory from MOTI_CODE_URL env var or use current directory."""
    code_url = os.environ.get("MOTI_CODE_URL")
    
    if not code_url:
        return os.getcwd()
    
    print(f"📦 CODE_URL detected, downloading code...")
    
    # Create a temp directory for extraction in /tmp
    extract_dir = tempfile.mkdtemp(prefix="moti_code_", dir="/tmp")
    
    try:
        return download_and_extract_zip(code_url, extract_dir)
    except Exception as e:
        print(f"✗ Failed to download/extract code: {e}")
        shutil.rmtree(extract_dir, ignore_errors=True)
        sys.exit(1)


def download_and_extract_zip(url, extract_dir):
    """Download a zip file and extract it."""
    zip_path = os.path.join(extract_dir, "code.zip")
    
    # Download the zip file
    print(f"⬇ Downloading zip...")
    request = urllib.request.Request(url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Moti/1.0)')
    
    # Add GitHub token if available (for private repos)
    github_token = os.environ.get("MOTI_GITHUB_TOKEN")
    if github_token:
        request.add_header('Authorization', f'Bearer {github_token}')
        print(f"🔑 Using GitHub token for authentication")
    
    with urllib.request.urlopen(request) as response:
        with open(zip_path, 'wb') as f:
            f.write(response.read())
    
    # Extract the zip
    print(f"📂 Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Remove the zip file
    os.remove(zip_path)
    
    # Find the extracted directory (usually there's a single folder inside)
    items = os.listdir(extract_dir)
    if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
        code_dir = os.path.join(extract_dir, items[0])
    else:
        code_dir = extract_dir
    
    return code_dir


def install_requirements(code_dir):
    """Install requirements.txt if it exists."""
    requirements_path = os.path.join(code_dir, "requirements/base.txt")
    
    if os.path.exists(requirements_path):
        print(f"📦 Installing dependencies from requirements.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path, "-q"],
            cwd=code_dir
        )
        if result.returncode != 0:
            print(f"✗ Failed to install dependencies")
            return False
        print(f"✓ Dependencies installed")
    return True


def start_foreground(code_dir=None, auto_install=True):
    """Start run.py in foreground."""
    if code_dir is None:
        code_dir = get_code_directory()
    
    # Auto-install requirements when MOTI_CODE_URL is used
    if auto_install and os.environ.get("MOTI_CODE_URL"):
        if not install_requirements(code_dir):
            return False
    
    run_py_path = os.path.join(code_dir, "run.py")
    
    if not os.path.exists(run_py_path):
        print(f"✗ run.py not found in {code_dir}")
        return False
    
    python_executable = sys.executable
    
    print(f"✓ Running run.py from {code_dir}")
    result = subprocess.run(
        [python_executable, run_py_path],
        cwd=code_dir,
    )
    return result.returncode == 0


def install_and_run():
    """Install dependencies from requirements.txt and run run.py."""
    code_dir = get_code_directory()
    
    # Install requirements
    if not install_requirements(code_dir):
        sys.exit(1)
    
    # Start run.py in foreground (skip auto_install since we just did it)
    if not start_foreground(code_dir, auto_install=False):
        sys.exit(1)


def main():
    """Main entry point - handle commands."""
    args = sys.argv[1:]
    
    # Check for MOTI_JOB_CONFIG environment variable (contains JSON config directly)
    config_json = os.environ.get("MOTI_JOB_CONFIG")
    
    # Load config and set env variables if available
    if config_json:
        load_and_set_config(config_json)
    
    if not args or args[0] in ("start", "run"):
        # Default: just start run.py
        if not start_foreground():
            sys.exit(1)
    elif args[0] == "install":
        # Install deps + start run.py
        install_and_run()
    else:
        print(f"Usage: moti [start|install]")
        print(f"  start   - Run run.py (default)")
        print(f"  install - Install requirements.txt and run run.py")
        print(f"")
        print(f"Environment Variables:")
        print(f"  MOTI_JOB_CONFIG   JSON config string")
        print(f"                    All JSON fields are set as MOTI_<KEY> env variables")
        sys.exit(1)


if __name__ == "__main__":
    main()
