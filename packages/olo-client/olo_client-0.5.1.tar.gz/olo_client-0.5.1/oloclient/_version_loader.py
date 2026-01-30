"""Version loader for setuptools - reads version without importing package dependencies."""
import re
from pathlib import Path

# Read version directly from _version.py file (no imports)
# Try multiple path resolution strategies
_version_file = None
_possible_paths = [
    Path(__file__).parent / "_version.py",  # Relative to this file
    Path(__file__).parent.parent / "oloclient" / "_version.py",  # From package root
    Path.cwd() / "oloclient" / "_version.py",  # From current working directory
]

for path in _possible_paths:
    if path.exists():
        _version_file = path
        break

if _version_file is None or not _version_file.exists():
    raise RuntimeError(
        f"Version file not found. Tried: {_possible_paths}. "
        f"Current file: {__file__}, CWD: {Path.cwd()}"
    )

try:
    _content = _version_file.read_text(encoding='utf-8')
except Exception as e:
    raise RuntimeError(f"Unable to read version file {_version_file}: {e}")

# Try to find version with regex
_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', _content)
if not _match:
    # Try alternative pattern
    _match = re.search(r'__version__\s*=\s*(["\'])([^"\']+)\1', _content)
    if _match and len(_match.groups()) >= 2:
        __version__ = _match.group(2)  # Get the version (second group)
    else:
        raise RuntimeError(
            f"Unable to find version in {_version_file}. "
            f"File exists: {_version_file.exists()}, "
            f"File content (first 200 chars):\n{_content[:200]}"
        )
else:
    __version__ = _match.group(1)  # Get the version (first group)

# Validate version is not empty
if not __version__ or not __version__.strip():
    raise RuntimeError(f"Version is empty in {_version_file}")

