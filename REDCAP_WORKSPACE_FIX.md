# Deleted REDCap assessment workspace update

This update changes server.py and static/app.js. It does not change REDCap forms,
delete REDCap records, or require a database migration.

## Behavior

- Refresh Countries explicitly checks REDCap and removes retained workspaces whose
  saved records are absent or now identify another country/period.
- Opening or creating a country assessment checks REDCap before using a retained
  saved workspace. Existing remote assessments are loaded from REDCap.
- Saving a previously saved workspace verifies its REDCap record first. If it is
  absent or changed, the retained workspace is cleared and the save returns 409.
  The browser displays the reason and reloads instead of retrying the old save.
- Empty successful REDCap exports are treated as no records. Connection failures,
  errors and invalid exports do not clear retained workspaces.
- Unsaved drafts are retained; they have no saved record to reconcile. Test Country
  remains temporary and does not require REDCap access.
- New records use random IDs to avoid reusing another record's ID after a service
  restart. A country/period already in REDCap cannot be silently duplicated.
- Updated coordinator browsers include the active workspace ID on API calls;
  writes from an outdated workspace are rejected before modifying it.

## Deploy

1. Stop testing and preserve any required unsaved entries. Have all users close old
   application tabs. Restarting discards temporary assessment workspaces.
2. Back up the installed application files and persistent configuration/database.
3. Replace server.py and static/app.js in the corresponding hosted source folders.
   Preserve .env, docker.env, the database, and Docker volumes.
4. Restart the application service. With the supplied compose.yaml deployment,
   rebuild/recreate the app using `docker compose up -d --build app` from the full
   deployment source directory (the update ZIP alone is not a Docker build context).
   Preserve any additional Compose options used by the administrator.
5. Open fresh tabs or hard-refresh so the updated JavaScript is loaded.

## Acceptance check in a separate REDCap testing project

1. Create a demonstration assessment, save one tool, and verify it directly in REDCap.
2. Delete that test record directly in REDCap, keeping the application tab open.
3. Try saving the old workspace: expect a deletion/change notice and no recreated record.
4. Click Refresh Countries: the deleted saved assessment should not appear.
5. Explicitly create that country/period again: expect a blank assessment.
6. Simulate a REDCap outage: expect a connection error and no workspace purge.
7. Verify two coordinator tabs: after one changes the active workspace, saving from
   the old tab should be rejected rather than applied to the new active workspace.

## Validation and limits

Run `python scripts/verify_deleted_redcap_workspace.py`,
`python scripts/verify_no_local_member_state.py`, `python -m py_compile server.py`,
and `node --check static/app.js`.
Regression checks use a separate database and mocked REDCap; no live records are changed.

This update does not fix server-to-REDCap network connectivity. It also does not
implement independent per-user server workspaces: the existing shared active
workspace architecture remains. The new workspace-ID guard reduces stale-tab
writes but is not full concurrent-user isolation. Verify/develop that separately
before simultaneous production assessments. REDCap does not make the existence
check and subsequent import atomic; coordinate external deletion with data entry.
