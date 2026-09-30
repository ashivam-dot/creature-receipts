"""Install or update the monitor's launchd job (every 15 minutes, and at login). It only reads.

    /usr/bin/python3 monitor/install.py            # install or update
    /usr/bin/python3 monitor/install.py --remove   # stop and remove
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = "com.creaturereceipts.monitor"
SOURCE = ROOT / "monitor" / f"{LABEL}.plist"
INSTALLED = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def main() -> None:
    domain = f"gui/{os.getuid()}"
    (ROOT / "monitor" / "out").mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
    if "--remove" in sys.argv:
        INSTALLED.unlink(missing_ok=True)
        print("monitor removed")
        return
    shutil.copyfile(SOURCE, INSTALLED)
    result = subprocess.run(["launchctl", "bootstrap", domain, str(INSTALLED)], capture_output=True, text=True)
    print("monitor installed" if result.returncode == 0 else f"bootstrap failed: {result.stderr.strip()}")


if __name__ == "__main__":
    main()
