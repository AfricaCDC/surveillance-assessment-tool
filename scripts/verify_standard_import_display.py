"""Regression check for immediate standard-workbook Inventory display."""

import base64
import os
import shutil
import sys
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
workbook_path = Path(r"C:\Users\George\Downloads\Surveillance System Profiling and Gap Analysis Tool 33SS.xlsx")
temporary_dir = Path(tempfile.mkdtemp(prefix="africa_cdc_import_test_"))
test_db = temporary_dir / "test.db"
shutil.copy2(root / "africa_cdc_web.db", test_db)
os.environ["AFRICA_CDC_DB_PATH"] = str(test_db)
sys.path.insert(0, str(root))

import server  # noqa: E402


server.initialize_database()
server.save_profile_phase(
    "phase1",
    {"country_name": "Test Country", "reporting_period": "July 2026", "comments": "", "tools": []},
)
file_data = {
    "name": workbook_path.name,
    "data": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,"
    + base64.b64encode(workbook_path.read_bytes()).decode("ascii"),
}
profile = server.import_phase1_excel(file_data)
phase1 = profile["phase1"]
names = [tool.get("inventory_name") for tool in phase1["tools"]]
assert phase1["country_name"] == "Test Country"
assert phase1["reporting_period"] == "July 2026"
assert len(names) == 14
assert names[:3] == ["HMIS/DHIS2", "EWARS", "GoDATA"]
assert "NPHI EVD_Dashboard and Screening" not in names

print("PASS: 14 Inventory tools load immediately for Test Country / July 2026")
server._RUNTIME_CONNECTION.close()
shutil.rmtree(temporary_dir, ignore_errors=True)
