# Africa CDC Shared Web Assessment

Current application version: **1.0.40**  
Profile-data format version: **3**

This is the web-based Africa CDC surveillance systems application covering Inventory, Profiling, and Gap Analysis.

## Open the source code in VS Code

Open `Africa CDC Web Assessment.code-workspace`, or open this entire folder in VS Code. Use **Run and Debug → Run Africa CDC Web App** to start it on port 8080. The source is separated as follows:

- `server.py`: HTTP API, REDCap assessment persistence, authentication, imports, and exports.
- `report_builder.py`: formatted Word report generation.
- `surveillance_app.py`: shared assessment and report logic.
- `static/index.html`: web page structure.
- `static/styles.css`: layout and Africa CDC visual styling.
- `static/app.js`: browser interactions, forms, charts, and reports.
- `africa_cdc_web.db`: accounts, permissions, groups, assignments, sessions, and configuration; preserve this file during code updates.

## Start the application

For Ubuntu VM hosting with Docker, follow [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md).
The Docker deployment includes persistent account storage, a health check, and an optional HTTPS proxy.

1. Double-click `start_web_app.bat` on the computer that will store the shared data.
2. The application opens at `http://127.0.0.1:8080`.
3. On the first launch, create the administrator account using a password of at least 6 characters, including a capital letter, lowercase letter, number and symbol.
4. Other devices on the same network open `http://SERVER-IP:8080`, replacing `SERVER-IP` with the host computer's IPv4 address, then sign in.

The server computer must remain running while participants enter information.

## Local Ollama report assistant

Ollama runs on the application server, not on each user's browser. The app calls the local Ollama HTTP API at `AFRICA_CDC_OLLAMA_URL` (default `http://127.0.0.1:11434`) and requests the exact model tag in `AFRICA_CDC_OLLAMA_MODEL` (default `qwen3:4b-instruct`). Upgrading the Ollama program normally requires no application change while its `/api/tags` and `/api/chat` endpoints remain compatible. Installing a different model does require changing the configured tag; the app does not silently switch models.

On the server, run `ollama ls` to see installed tags. Set `AFRICA_CDC_OLLAMA_MODEL` to the tag you choose in the application-adjacent `.env` file (or in the deployment's environment file), and restart the application. Keep `AFRICA_CDC_OLLAMA_URL` on loopback when Ollama runs on the same server. In the app's assistant provider settings, use **Test provider** to check availability. Test a generated report as well, because a newer or larger model can change response quality, memory use, and response time. If Ollama or the configured model is unavailable, the report assistant uses its built-in response path.

## Authentication

The first person to open a new installation creates the administrator account using either a username or an email address. New and reset passwords are stored only as salted Argon2id hashes in the `users` table, never as readable text or in country-project snapshots. Existing PBKDF2 hashes are upgraded after the next successful login. Successful sign-in creates an HTTP-only session cookie that expires after 12 hours. Password resets invalidate that user's sessions, and expired sessions are removed automatically. Use **Log out** in the application header when leaving a shared computer.

For production, set a long random server-side pepper before creating or upgrading accounts. In PowerShell, run the following once, then restart PowerShell and the application:

```powershell
$bytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
$pepper = [Convert]::ToBase64String($bytes)
setx AFRICA_CDC_PASSWORD_PEPPER $pepper
```

Store that value in the organisation's password manager or secret manager. Do not put it in this folder, source control, logs, or database backups. Losing or changing it prevents existing Argon2id passwords from being verified. When serving the app over HTTPS, also set `AFRICA_CDC_SECURE_COOKIES=true`.

Participant credentials are deliberately not retained in country snapshots. After switching back to a country, an administrator must use the account reset control to issue fresh credentials to each participant group.

## REDCap-primary storage

The application loads private REDCap settings from a local `.env` file and writes every successful Member State assessment save directly to REDCap. The reserved **Test Country** workspace is temporary in memory and is never written to REDCap. Create the private file in PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace the placeholder token and pepper in `.env`, then save it. The adjacent `.env` is authoritative for desktop, source, and packaged launches; preserve it during updates so password verification remains stable. Member State assessment saves are written directly to REDCap. Keep `AFRICA_CDC_REDCAP_AUTO_SYNC_MINUTES=0`; background synchronization is disabled in REDCap-primary mode.

REDCap is the primary assessment database. Loading a country-period retrieves its current REDCap record; each Save must receive REDCap confirmation before the application reports success. When REDCap is unavailable, the save fails and the browser retains the entered values for retry. The `.env` file contains secrets in readable form, so keep it only on the server, restrict access to the Windows account running the application and authorised administrators, and include its values separately in the organisation's secret-management process rather than ordinary database backups.

For non-production form testing, select **Test Country**. Its saves and imports show a temporary-only status, never create or update a REDCap record, and disappear when the application closes or restarts. Use a separately approved UAT country when testing REDCap persistence itself.

## Features

- Inventory with any number of HIS tools and systems.
- Detailed Profiling automatically linked to every named Inventory system.
- All desktop Profiling questions, single-select dropdowns, multiselect option panels, and custom responses.
- Open and save complete JSON assessment profiles.
- Import a complete desktop workbook or import Inventory, Profiling, and Gap Analysis separately.
- Three default groups, with the ability to add more.
- Exclusive group assignment for each of the nine Gap Analysis domains.
- Simultaneous entry from computers, tablets, and phones.
- SQLite stores application accounts, sessions, groups, assignments, and configuration only. Assessment profiles and responses are held temporarily in memory and persisted directly to REDCap.
- Autosave and explicit save controls.
- Multiple Excel workbook import and merged non-empty responses.
- Live completion dashboard.
- Gap Analysis gaps and recommendations summary report, independent of Inventory and Profiling.
- Full Inventory/Profiling report with assessment completeness, gaps, strengths, recommendations, and action plans.
- Separate Inventory and Profiling Excel exports, combined Excel export, TXT, DOCX, and browser print/PDF output.

## Data and backup

Application accounts, password hashes, sessions, groups, assignments, country indexes, and configuration are stored in `africa_cdc_web.db`. Assessment profiles and responses are not persisted there. Database files, journals, local environment files, and backup directories are excluded from Git. Restrict this folder to the Windows account running the application and authorised administrators.

Stop the server before copying the database. Store every backup only on an encrypted volume approved by the organisation, such as a BitLocker-protected Windows drive or an access-controlled encrypted backup service. Limit access, define a retention period, and periodically test restoration on an isolated computer. Do not place database copies in an unencrypted sync folder or allow multiple servers to write to the same database.

## Network access

If other devices cannot connect, allow Python through Windows Firewall for private networks and confirm all devices are connected to the same network.

