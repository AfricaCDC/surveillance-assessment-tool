"""Delete every REDCap assessment record for one exact country name."""

import argparse
import sys
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import server  # noqa: E402


parser = argparse.ArgumentParser()
parser.add_argument("country")
parser.add_argument("--execute", action="store_true")
args = parser.parse_args()

rows = server.redcap_request({
    "content": "record",
    "type": "flat",
    "rawOrLabel": "raw",
    "rawOrLabelHeaders": "raw",
    "exportDataAccessGroups": "false",
})
main_rows = [row for row in rows if not str(row.get("redcap_repeat_instrument") or "").strip()]
matches = [
    row for row in main_rows
    if str(row.get("country_name") or "").strip().casefold() == args.country.strip().casefold()
]
targets = sorted({str(row.get("record_id") or "").strip() for row in matches if str(row.get("record_id") or "").strip()})

print(f"COUNTRY={args.country}")
print(f"RECORDS={len(targets)}")
for row in matches:
    print(f"TARGET={row.get('record_id')} | {row.get('reporting_period')}")

if args.execute:
    for record_id in targets:
        server.redcap_request({"content": "record", "action": "delete", "records[0]": record_id})
    print(f"DELETED={len(targets)}")
