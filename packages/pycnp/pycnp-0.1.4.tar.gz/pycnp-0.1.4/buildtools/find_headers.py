"""Find header files in a directory (cross-platform)."""

import glob
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("")
    sys.exit(0)

search_dir = Path(sys.argv[1])
if not search_dir.exists():
    print("")
    sys.exit(0)

try:
    headers = glob.glob(str(search_dir / "**" / "*.h"), recursive=True)
    headers = [Path(h).as_posix() for h in headers]
    output = " ".join(headers)
    sys.stdout.buffer.write(output.encode("utf-8", "surrogatepass"))
except Exception:
    sys.stdout.buffer.write(b"")
