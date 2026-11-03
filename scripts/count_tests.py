"""Print the test total from a real pytest collection run."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    total = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line and "::" in line and line.endswith("]") is False:
            total += 1
    # Fall back to the summary line pytest prints ("N tests collected").
    if total == 0:
        for line in proc.stdout.splitlines():
            if "collected" in line:
                print(line.strip())
                return 0
    print(f"tests collected: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
