"""Whether a scheduled studio.yml run is needed. Modal runs the studio (cloud.studio_run); GitHub fills in only
when the last run on Modal failed or is older than FRESH_HOURS, so the two don't do the same work."""

import datetime as dt
import json
import os
from pathlib import Path

# Modal's runs are 6 hours apart and take minutes; this workflow's schedule is 2 hours behind theirs.
FRESH_HOURS = 8

path = Path("status/status.json")
# A new channel has no status yet, so its first scheduled run goes ahead here.
status = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"updated_at": "1970-01-01T00:00:00+00:00"}
run = status.get("run") or {}
age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(status["updated_at"])
fresh = run.get("host") == "modal" and status.get("result") != "failed" and age < dt.timedelta(hours=FRESH_HOURS)
print(f"last studio run: on {run.get('host')}, {status.get('result')}, {age.total_seconds() / 3600:.1f} hours ago; "
      + ("Modal is running the studio, nothing to do" if fresh else "running it here"))
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
    out.write(f"skip={'true' if fresh else 'false'}\n")
