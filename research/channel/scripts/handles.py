"""Check YouTube handle availability by HTTP status of https://www.youtube.com/@HANDLE (404 = likely free)."""
import subprocess
import sys
import time

for h in sys.argv[1:]:
    code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://www.youtube.com/@{h}"],
                          capture_output=True, text=True).stdout
    print(f"@{h}: {code}")
    time.sleep(0.5)
