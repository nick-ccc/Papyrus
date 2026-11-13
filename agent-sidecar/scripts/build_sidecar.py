"""Build the sidecar with PyInstaller and place it where Tauri expects it.

Tauri's `externalBin` needs `src-tauri/binaries/papyrus-agent-<target-triple>[.exe]`.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BINARIES_DIR = ROOT.parent / "src-tauri" / "binaries"
NAME = "papyrus-agent"


def host_triple() -> str:
    out = subprocess.run(
        ["rustc", "-vV"], check=True, capture_output=True, text=True
    ).stdout
    match = re.search(r"^host: (\S+)$", out, re.MULTILINE)
    if not match:
        raise SystemExit("Could not determine target triple from `rustc -vV`")
    return match.group(1)


def main() -> None:
    triple = sys.argv[1] if len(sys.argv) > 1 else host_triple()
    suffix = ".exe" if "windows" in triple else ""

    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--distpath", str(ROOT / "dist"),
            "--workpath", str(ROOT / "build"),
            str(ROOT / "papyrus-agent.spec"),
        ],
        check=True,
        cwd=ROOT,
    )

    BINARIES_DIR.mkdir(parents=True, exist_ok=True)
    target = BINARIES_DIR / f"{NAME}-{triple}{suffix}"
    shutil.copy2(ROOT / "dist" / f"{NAME}{suffix}", target)
    print(f"Sidecar written to {target}")


if __name__ == "__main__":
    main()
