"""Extract version from pyproject.toml."""

import re
import sys
from pathlib import Path

try:
    # Get the directory containing this script, then go up to project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    pyproject = project_root / "pyproject.toml"

    if not pyproject.exists():
        # Fallback: try current working directory
        pyproject = Path.cwd() / "pyproject.toml"

    if not pyproject.exists():
        print("0.0.0", file=sys.stdout)
        sys.exit(0)

    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        print(match.group(1), file=sys.stdout)
    else:
        print("0.0.0", file=sys.stdout)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
