import re
import sys
from pathlib import Path

def bump_version():
    toml_path = Path("pyproject.toml")
    if not toml_path.exists():
        print("pyproject.toml not found")
        sys.exit(1)

    content = toml_path.read_text()
    
    # regex to find version = "x.y.z"
    pattern = r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
    match = re.search(pattern, content)
    
    if not match:
        print("Version pattern not found in pyproject.toml")
        sys.exit(1)
        
    major, minor, patch = map(int, match.groups())
    new_patch = patch + 1
    new_version = f'{major}.{minor}.{new_patch}'
    
    new_content = re.sub(pattern, f'version = "{new_version}"', content)
    toml_path.write_text(new_content)
    
    # Update __init__.py
    init_path = Path("jeomaechu/__init__.py")
    if init_path.exists():
        init_content = init_path.read_text()
        init_pattern = r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
        new_init_content = re.sub(init_pattern, f'__version__ = "{new_version}"', init_content)
        init_path.write_text(new_init_content)

    print(new_version)

if __name__ == "__main__":
    bump_version()
