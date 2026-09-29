"""Print Profiling coverage values for one REDCap country-period record."""

import argparse
import sys
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import server  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("country")
parser.add_argument("period")
args = parser.parse_args()

rows = server.redcap_request({
    "content": "record", "type": "flat", "rawOrLabel": "raw",
    "rawOrLabelHeaders": "raw", "exportDataAccessGroups": "false",
})
main = [row for row in rows if not str(row.get("redcap_repeat_instrument") or "").strip()]
matches = [row for row in main if str(row.get("country_name") or "").strip().casefold() == args.country.casefold()
           and str(row.get("reporting_period") or "").strip().casefold() == args.period.casefold()]
if not matches:
    raise SystemExit("No matching country-period record")
record_id = str(matches[0].get("record_id") or "")
profiles = [row for row in rows if str(row.get("record_id") or "") == record_id
            and str(row.get("redcap_repeat_instrument") or "") == "system_profiling"]
print(f"RECORD={record_id} PROFILES={len(profiles)}")
for row in profiles:
    print(f"{row.get('official_name') or '(unnamed)'} | coverage={row.get('coverage_level')!r}")
