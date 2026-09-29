"""Clear locally cached assessment records while preserving accounts and settings."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


db_path = Path(__file__).resolve().parents[1] / "africa_cdc_web.db"
now = datetime.now(timezone.utc).isoformat(timespec="seconds")

with sqlite3.connect(db_path) as db:
    db.execute("PRAGMA foreign_keys=OFF")
    counts_before = {
        table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "country_projects",
            "profile_data",
            "responses",
            "assignments",
            "inventory_tool_assignments",
            "profiling_tool_assignments",
        )
    }
    assessment = db.execute("SELECT id FROM assessments ORDER BY id LIMIT 1").fetchone()
    assessment_id = assessment[0]
    for table in (
        "responses",
        "assignments",
        "inventory_tool_assignments",
        "profiling_tool_assignments",
        "groups",
        "profile_data",
        "country_projects",
    ):
        db.execute(f"DELETE FROM {table}")
    db.execute(
        "UPDATE assessments SET title=?, scope=? WHERE id=?",
        ("Africa CDC Gap Analysis", "", assessment_id),
    )
    for name in ("Group 1", "Group 2", "Group 3"):
        db.execute(
            "INSERT INTO groups(assessment_id,name) VALUES(?,?)",
            (assessment_id, name),
        )
    cursor = db.execute(
        "INSERT INTO country_projects(country_name,reporting_period,title,payload,redcap_record_id,created_at,updated_at) "
        "VALUES('','','Country Assessment',NULL,NULL,?,?)",
        (now, now),
    )
    db.execute(
        "INSERT INTO app_settings(key,value) VALUES('active_project_id',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(cursor.lastrowid),),
    )
    db.commit()
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

print("Cleared local assessment data:", counts_before)
