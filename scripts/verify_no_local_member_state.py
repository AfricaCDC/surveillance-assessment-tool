"""Regression check: Member State assessment data must never persist locally."""

import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path


source_db = Path(__file__).resolve().parents[1] / "africa_cdc_web.db"
sys.path.insert(0, str(source_db.parent))
temporary_dir = Path(tempfile.mkdtemp(prefix="africa_cdc_storage_test_"))
test_db = temporary_dir / "test.db"
shutil.copy2(source_db, test_db)
os.environ["AFRICA_CDC_DB_PATH"] = str(test_db)

import server  # noqa: E402


server.initialize_database()
with server.connect() as runtime:
    project_id = runtime.execute("SELECT id FROM country_projects LIMIT 1").fetchone()[0]
    runtime.execute(
        "UPDATE country_projects SET country_name='Persistence Test',reporting_period='August 2026',payload='member-data' WHERE id=?",
        (project_id,),
    )
    runtime.execute(
        "INSERT INTO profile_data(phase,payload,updated_at) VALUES('phase1','member-data',?)",
        (server.utc_now(),),
    )

with sqlite3.connect(test_db) as disk:
    assert disk.execute("SELECT COUNT(*) FROM profile_data").fetchone()[0] == 0
    assert disk.execute("SELECT COUNT(*) FROM responses").fetchone()[0] == 0
    assert disk.execute("SELECT COUNT(*) FROM assignments").fetchone()[0] == 0
    assert disk.execute("SELECT COUNT(*) FROM inventory_tool_assignments").fetchone()[0] == 0
    assert disk.execute("SELECT COUNT(*) FROM profiling_tool_assignments").fetchone()[0] == 0
    assert disk.execute("SELECT COUNT(*) FROM country_projects WHERE country_name<>'' OR reporting_period<>'' OR payload IS NOT NULL").fetchone()[0] == 0

print("PASS: no Member State assessment data was persisted locally")
server._RUNTIME_CONNECTION.close()
shutil.rmtree(temporary_dir, ignore_errors=True)
