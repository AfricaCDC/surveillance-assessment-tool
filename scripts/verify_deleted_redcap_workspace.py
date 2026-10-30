"""Deletion reconciliation regression tests; isolated database and mocked REDCap only."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

with tempfile.TemporaryDirectory(prefix="deleted_redcap_test_") as temporary:
    os.environ["AFRICA_CDC_DB_PATH"] = str(Path(temporary) / "test.db")
    import server

    server.initialize_database()
    rows = []
    writes = []

    def redcap(parameters):
        if "data" in parameters:
            writes.append(json.loads(parameters["data"]))
            return 1
        return rows

    def saved_workspace(country="Algeria", record="acdc-old"):
        with patch.object(server, "redcap_request", side_effect=redcap):
            server.create_country_project(country, "October 2026")
        payload = server.blank_project_payload(country, "October 2026", "Dummy assessment")
        payload["profile"]["phase1"]["tools"] = [{"_id": "dummy", "inventory_name": "Dummy tool"}]
        server.restore_project(payload, reset_group_accounts=False)
        server.capture_active_project()
        with server.connect() as db:
            db.execute("UPDATE country_projects SET redcap_record_id=? WHERE id=?", (record, server.active_project_id()))
        return server.active_project_id()

    try:
        with patch.object(server, "redcap_request", side_effect=redcap):
            old_id = saved_workspace()
            before = server.profile_state()
            # An outage or malformed response must never be interpreted as deletion.
            for response in (RuntimeError("offline"), {"error": "denied"}, [{"record_id": "acdc-old"}]):
                with patch.object(server, "redcap_request", side_effect=response if isinstance(response, Exception) else None,
                                  return_value=None if isinstance(response, Exception) else response):
                    try:
                        server.reconcile_retained_projects()
                        raise AssertionError("Invalid response accepted")
                    except RuntimeError:
                        pass
                assert server.profile_state() == before
                assert server.active_project_id() == old_id

            # An acknowledged empty project invalidates an old save without importing data.
            try:
                server.sync_current_project_to_redcap()
                raise AssertionError("Deleted record save accepted")
            except server.DeletedRedcapRecord:
                pass
            assert not writes
            assert server.active_project_id() != old_id
            assert not server.profile_state()["phase1"]["tools"]
            assert not server.country_projects_state()["projects"]
            # Same country/period can now be explicitly started again.
            server.create_country_project("Algeria", "October 2026")
            assert not server.profile_state()["phase1"]["tools"]
            server.sync_current_project_to_redcap()
            assert len(writes) == 1
            assert writes[0][0]["record_id"] != "acdc-old"
            rows[:] = [writes[0][0]]
            server.sync_current_project_to_redcap()
            assert writes[1][0]["record_id"] == rows[0]["record_id"]
            # A record elsewhere in REDCap cannot be silently duplicated.
            with server.connect() as db:
                db.execute("UPDATE country_projects SET redcap_record_id=NULL WHERE id=?", (server.active_project_id(),))
            try:
                server.sync_current_project_to_redcap()
                raise AssertionError("Duplicate save accepted")
            except ValueError as error:
                assert "already exist" in str(error)
            assert len(writes) == 2
            # Temporary Test Country still works without a REDCap connection.
            with patch.object(server, "redcap_request", side_effect=AssertionError("Unexpected network request")):
                server.create_country_project("Test Country", "October 2026")
                assert server.sync_current_project_to_redcap()["temporary"]
        print("PASS: deletion blocks recreation; cleanup, fresh saves, outage preservation, duplicate prevention and Test Country")
    finally:
        server._RUNTIME_CONNECTION.close()
        server._RUNTIME_CONNECTION = None
