# Africa CDC Assessment Web Application

## Windows Server production deployment guide

This guide deploys one central application instance on Windows Server 2019, 2022 or 2025. IIS provides the public HTTPS address and forwards requests to the Python application on `127.0.0.1:8080`.

```text
Users' browsers
      |
      | HTTPS (port 443)
      v
Microsoft IIS + URL Rewrite + ARR
      |
      | http://127.0.0.1:8080 (server-local only)
      v
Africa CDC Python application
      |-- SQLite authentication and recovery cache
      `-- HTTPS connection to Africa CDC REDCap API
```

REDCap is the authoritative assessment-data store. The local SQLite database stores application accounts, sessions, settings and recovery data.

### Version 1.0.42 operating rules

- Member State assessment saves require REDCap confirmation; failed saves leave entered values in the browser for retry.
- The exact country name **Test Country** is temporary in memory, is never sent to REDCap, and is discarded when the application restarts.
- Use a separately approved UAT country name to test REDCap persistence.
- Profiling imports retain Response and Comments for every question, display immediately, and preserve blank dropdowns as **No response**.
- National-coverage summaries count only explicit national-level Profiling responses.
- The application-adjacent `.env`, when present, is authoritative. Do not maintain conflicting password-security values in machine environment variables and `.env`.

Give application administrators and data-entry clerks the plain-language `USER_MANUAL.md` after deployment.

Use `APPLICATION_UPDATE_GUIDE.md` for every future production update.

## 1. Obtain the required infrastructure information

Before starting, obtain:

- Windows Server 2019, 2022 or 2025 with current security updates.
- Local administrator access during installation.
- A static server IP address.
- A DNS name, recommended: `assessment.africacdc.org`.
- A DNS record pointing the name to the server.
- An SSL/TLS certificate for that DNS name.
- Inbound ports 80 and 443 permitted by the network firewall.
- Outbound HTTPS access to `tools.africacdc.org`.
- The REDCap API token for PID 932.
- A protected backup destination.
- A dedicated Windows service account, recommended: `svc_africacdc`.

Do not place the REDCap token in email, tickets, screenshots, the application source, IIS configuration or this guide.

## 2. Install Windows components

Open **Windows PowerShell as Administrator**.

Install IIS and its management tools:

```powershell
Install-WindowsFeature Web-Server,Web-Mgmt-Console -IncludeManagementTools
```

Install the current supported 64-bit Python 3 release for all users from:

```text
https://www.python.org/downloads/windows/
```

During installation:

- Select **Install for all users**.
- Select **Add Python to PATH**.
- Record the installed Python path.

Install these Microsoft IIS extensions using their official installers:

- IIS URL Rewrite Module 2
- IIS Application Request Routing (ARR)

Microsoft's reverse-proxy documentation lists URL Rewrite and ARR as prerequisites: https://learn.microsoft.com/en-us/iis/extensions/url-rewrite-module/reverse-proxy-with-url-rewrite-v2-and-application-request-routing

Restart IIS Manager after installing the extensions.

## 3. Create the service account

Ask the IT/domain team to create a dedicated account such as:

```text
DOMAIN\svc_africacdc
```

The account requires:

- **Log on as a batch job** permission.
- Read and execute access to `C:\Apps\AfricaCDCAssessment`.
- Modify access to `C:\ProgramData\AfricaCDC\Assessment`.
- No interactive administrator rights.

For a standalone server, IT may create a local service account instead. Follow the organisation's password rotation and managed-service-account policy.

## 4. Create application and data directories

Run in elevated PowerShell:

```powershell
New-Item -ItemType Directory -Path 'C:\Apps\AfricaCDCAssessment' -Force
New-Item -ItemType Directory -Path 'C:\ProgramData\AfricaCDC\Assessment' -Force
New-Item -ItemType Directory -Path 'C:\ProgramData\AfricaCDC\Assessment\Backups' -Force
New-Item -ItemType Directory -Path 'C:\inetpub\AfricaCDCAssessmentProxy' -Force
```

Use **File Explorer → Properties → Security** to grant:

- Application directory: Read & Execute to the service account.
- Data directory: Modify to the service account.
- Backup directory: Modify to the service account and access only to authorised administrators/backup services.

Remove unnecessary write permissions from the application source directory.

## 5. Copy the application

Copy the complete application folder contents into:

```text
C:\Apps\AfricaCDCAssessment
```

Confirm that these files exist:

```text
C:\Apps\AfricaCDCAssessment\server.py
C:\Apps\AfricaCDCAssessment\requirements.txt
C:\Apps\AfricaCDCAssessment\standard_assessment_template.xlsx
C:\Apps\AfricaCDCAssessment\static\index.html
```

Do not place the writable production database inside the source directory.

## 6. Create the Python virtual environment

In elevated PowerShell:

```powershell
Set-Location -LiteralPath 'C:\Apps\AfricaCDCAssessment'
python -m venv .venv
& 'C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe' -m pip install --upgrade pip
& 'C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe' -m pip install -r 'C:\Apps\AfricaCDCAssessment\requirements.txt'
```

Validate the source:

```powershell
& 'C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe' -m py_compile 'C:\Apps\AfricaCDCAssessment\server.py'
```

## 7. Prepare the local database

For a new installation, the application creates the database automatically at the configured path.

To preserve the existing administrator and clerk accounts, stop the old application and copy only its main database file:

```powershell
Copy-Item -LiteralPath 'C:\PATH\TO\OLD\africa_cdc_web.db' -Destination 'C:\ProgramData\AfricaCDC\Assessment\africa_cdc_web.db'
```

Do not copy `africa_cdc_web.db-wal` or `africa_cdc_web.db-shm` from a running application. Create a consistent backup or stop the old instance first.

After copying, confirm that the service account has Modify permission on the database and its parent directory.

## 8. Configure production environment variables

The application reads these machine-level variables:

```text
AFRICA_CDC_DB_PATH=C:\ProgramData\AfricaCDC\Assessment\africa_cdc_web.db
AFRICA_CDC_REDCAP_TOKEN=<REDCAP TOKEN FOR PID 932>
AFRICA_CDC_SECURE_COOKIES=1
```

Recommended method:

1. Open **System Properties**.
2. Select **Advanced → Environment Variables**.
3. Under **System variables**, create the three variables above.
4. Paste the token directly on the server.
5. Close the dialog and do not record the token elsewhere.

Machine-level environment variables can be read by local administrators. Restrict server administrator membership and follow Africa CDC secret-management policy. If the organisation has a managed secrets platform, use it to populate the process environment instead.

Restart the server after creating the variables so the scheduled task receives them.

## 9. Test the Python application locally

After restarting, open elevated PowerShell:

```powershell
Set-Location -LiteralPath 'C:\Apps\AfricaCDCAssessment'
& '.\.venv\Scripts\python.exe' '.\server.py' --host 127.0.0.1 --port 8080 --no-browser
```

In another PowerShell window:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8080/health'
```

Expected result:

```text
status
------
ok
```

Press `Ctrl+C` in the first window after the test. Confirm that no process remains listening:

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
```

## 10. Configure automatic startup with Task Scheduler

Microsoft documents startup triggers and task creation through `schtasks`: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create

Use the graphical Task Scheduler so restart and concurrency settings can be reviewed clearly:

1. Open **Task Scheduler** as administrator.
2. Select **Task Scheduler Library → Create Task**.
3. General tab:
   - Name: `Africa CDC Assessment Web Application`
   - Select **Run whether user is logged on or not**.
   - Select **Run with highest privileges** only if required by IT policy.
   - Configure for the installed Windows Server version.
   - Use the dedicated service account.
4. Triggers tab:
   - New trigger: **At startup**.
   - Add a delay of 30 seconds.
5. Actions tab:
   - Program/script: `C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe`
   - Add arguments: `server.py --host 127.0.0.1 --port 8080 --no-browser`
   - Start in: `C:\Apps\AfricaCDCAssessment`
6. Conditions tab:
   - Clear settings that stop the task when the server switches power state, unless required by policy.
7. Settings tab:
   - Allow task to be run on demand.
   - If the task fails, restart every 1 minute.
   - Attempt restart at least 3 times.
   - Clear **Stop the task if it runs longer than...**.
   - If the task is already running: **Do not start a new instance**.
8. Save and supply the service-account password if requested.
9. Right-click the task and select **Run**.

Validate:

```powershell
Get-ScheduledTask -TaskName 'Africa CDC Assessment Web Application'
Get-NetTCPConnection -LocalPort 8080 -State Listen
Invoke-RestMethod 'http://127.0.0.1:8080/health'
```

There must be exactly one listener on port 8080.

## 11. Enable IIS reverse proxy

1. Open **IIS Manager**.
2. Select the server name.
3. Open **Application Request Routing Cache**.
4. Select **Server Proxy Settings**.
5. Select **Enable proxy**.
6. Select **Preserve host header** if available.
7. Apply the change.

ARR uses URL Rewrite rules to forward requests to the application. This is the architecture documented by Microsoft: https://learn.microsoft.com/en-us/iis/extensions/planning-for-arr/using-the-application-request-routing-module

## 12. Create the IIS proxy configuration

Create this file:

```text
C:\inetpub\AfricaCDCAssessmentProxy\web.config
```

Contents:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <security>
      <requestFiltering>
        <requestLimits maxAllowedContentLength="52428800" />
      </requestFiltering>
    </security>
    <rewrite>
      <rules>
        <rule name="Redirect HTTP to HTTPS" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{HTTPS}" pattern="off" ignoreCase="true" />
          </conditions>
          <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
        </rule>
        <rule name="Reverse proxy to Africa CDC assessment" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:8080/{R:1}" appendQueryString="true" />
        </rule>
      </rules>
    </rewrite>
    <httpProtocol>
      <customHeaders>
        <add name="X-Content-Type-Options" value="nosniff" />
        <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
      </customHeaders>
    </httpProtocol>
  </system.webServer>
</configuration>
```

## 13. Create the IIS website

In IIS Manager:

1. Right-click **Sites → Add Website**.
2. Site name: `Africa CDC Assessment`.
3. Physical path: `C:\inetpub\AfricaCDCAssessmentProxy`.
4. Binding type: `http`.
5. Port: `80`.
6. Host name: `assessment.africacdc.org`.
7. Create a dedicated application pool.
8. Set the pool's **.NET CLR Version** to **No Managed Code**.
9. Keep the application pool running; IIS only proxies requests and does not execute Python.

Run:

```powershell
Import-Module WebAdministration
Test-Path 'IIS:\Sites\Africa CDC Assessment'
```

## 14. Install and bind the HTTPS certificate

Obtain a certificate for `assessment.africacdc.org` from the Africa CDC enterprise certificate authority or an approved public certificate authority.

In IIS Manager:

1. Select the server → **Server Certificates**.
2. Import or complete the certificate request.
3. Select **Sites → Africa CDC Assessment → Bindings**.
4. Add binding type `https`, port `443`.
5. Enter host name `assessment.africacdc.org`.
6. Select **Require Server Name Indication** when the server hosts multiple HTTPS sites.
7. Select the correct certificate.
8. Save.

Microsoft's IIS SSL guidance covers obtaining a certificate and creating an HTTPS binding: https://learn.microsoft.com/en-us/iis/manage/configuring-security/how-to-set-up-ssl-on-iis

## 15. Configure Windows Firewall

Allow only IIS web traffic. Do not create an inbound rule for port 8080.

Run in elevated PowerShell:

```powershell
New-NetFirewallRule -DisplayName 'Africa CDC Assessment HTTP' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80 -Profile Domain,Private
New-NetFirewallRule -DisplayName 'Africa CDC Assessment HTTPS' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 443 -Profile Domain,Private
```

If the server is intentionally internet-facing, IT must choose the appropriate firewall profile and restrict source networks where possible. Microsoft documents `New-NetFirewallRule` here: https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule

Confirm that port 8080 is bound only to loopback:

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```

`LocalAddress` must be `127.0.0.1`, not `0.0.0.0`.

## 16. Verify the production website

Open:

```text
https://assessment.africacdc.org/login
```

Complete this checklist:

1. HTTP redirects to HTTPS.
2. The browser shows a trusted certificate.
3. The login screen appears first.
4. The administrator can sign in.
5. Existing countries appear.
6. REDCap shows `https://tools.africacdc.org/africacdcrc/api/`.
7. **Test connection** succeeds.
8. Saving an approved persistent UAT country succeeds.
9. The matching `acdc-N` record appears in REDCap; a separate **Test Country** check creates no REDCap record.
10. **Load current country from REDCap** restores matching counts.
11. A clerk sees only its assigned phase and items.
12. Logout returns to `/login`.

## 17. Configure daily backups

Create:

```text
C:\Apps\AfricaCDCAssessment\backup_database.ps1
```

Contents:

```powershell
$ErrorActionPreference = 'Stop'
$database = 'C:\ProgramData\AfricaCDC\Assessment\africa_cdc_web.db'
$backupDirectory = 'C:\ProgramData\AfricaCDC\Assessment\Backups'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$backup = Join-Path $backupDirectory "africa_cdc_web_$timestamp.db"
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
$python = 'C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe'
$script = "import sqlite3; source=sqlite3.connect(r'$database'); target=sqlite3.connect(r'$backup'); source.backup(target); target.close(); source.close()"
& $python -c $script
if ($LASTEXITCODE -ne 0) { throw 'SQLite backup failed' }
Get-ChildItem -LiteralPath $backupDirectory -Filter 'africa_cdc_web_*.db' |
  Where-Object LastWriteTimeUtc -lt (Get-Date).ToUniversalTime().AddDays(-30) |
  Remove-Item -Force
```

Create a second scheduled task:

- Name: `Africa CDC Assessment Database Backup`
- Trigger: Daily at 01:15
- Program: `powershell.exe`
- Arguments: `-NoProfile -ExecutionPolicy Bypass -File "C:\Apps\AfricaCDCAssessment\backup_database.ps1"`
- Run as an approved backup/service account.
- Run whether the user is logged on or not.

Run the task manually and confirm that a valid `.db` file appears in the backup directory. Copy backups to an encrypted off-server destination according to Africa CDC policy. Test restoration before production launch.

## 18. Application updates

Before updating:

1. Run the backup task manually.
2. Confirm REDCap synchronization is current.
3. Stop the application task:

```powershell
Stop-ScheduledTask -TaskName 'Africa CDC Assessment Web Application'
```

4. Verify port 8080 is no longer listening.
5. Copy new source files into `C:\Apps\AfricaCDCAssessment`.
6. Do not overwrite the database in `C:\ProgramData` or machine environment variables.
7. Update dependencies:

```powershell
& 'C:\Apps\AfricaCDCAssessment\.venv\Scripts\python.exe' -m pip install -r 'C:\Apps\AfricaCDCAssessment\requirements.txt'
```

8. Start and verify:

```powershell
Start-ScheduledTask -TaskName 'Africa CDC Assessment Web Application'
Start-Sleep -Seconds 3
Invoke-RestMethod 'http://127.0.0.1:8080/health'
```

## 19. Troubleshooting

### IIS returns HTTP 502

Check whether the Python process is running:

```powershell
Get-ScheduledTaskInfo -TaskName 'Africa CDC Assessment Web Application'
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
Invoke-RestMethod 'http://127.0.0.1:8080/health'
```

Review **Event Viewer → Applications and Services Logs → Microsoft → Windows → TaskScheduler**.

### Multiple port-8080 listeners

The task must use **Do not start a new instance**. Stop manually launched copies and keep one scheduled instance only. Do not use the desktop `start_web_app.bat` on the server.

### REDCap connection fails

- API URL must be exactly `https://tools.africacdc.org/africacdcrc/api/`.
- Confirm outbound TCP 443 to `tools.africacdc.org`.
- Confirm the token belongs to PID 932 and has import/export rights.
- Restart the scheduled task after changing the machine token variable.

### REDCap save fails

- Keep the browser page open; entered values remain available there for retry.
- Restore network/API access and repeat the save.
- Verify the matching `acdc-N` record before leaving the assessment.
- Do not treat **Test Country: temporary only - not saved to REDCap** as a failure.

### Token rotation

1. Generate and approve the replacement token in REDCap.
2. Replace the machine-level `AFRICA_CDC_REDCAP_TOKEN` value.
3. Restart the scheduled task.
4. Test the REDCap connection.
5. Save and reload an approved persistent UAT assessment. Do not use the reserved **Test Country** name.

## 20. Responsibilities

### Application administrator

- Creates countries and groups.
- Assigns tools and domains.
- Manages clerk accounts.
- Reviews REDCap synchronization and completeness.

### Windows Server/IIS administrator

- Maintains Windows, IIS, ARR, URL Rewrite, DNS and certificates.
- Controls environment variables and server administrators.
- Monitors the scheduled tasks and storage.
- Tests backups and restores.
- Applies application and security updates.

### REDCap system administrator

- Maintains PID 932 and API permissions.
- Maintains the REDCap API endpoint.
- Reviews project access and REDCap audit logs.

## Final Windows production handover checklist

- [ ] One central scheduled application instance only.
- [ ] DNS points to the Windows server.
- [ ] Trusted HTTPS certificate is installed.
- [ ] HTTP redirects to HTTPS.
- [ ] IIS ARR proxy is enabled.
- [ ] Port 8080 listens on `127.0.0.1` only.
- [ ] No inbound firewall rule exposes port 8080.
- [ ] Secure cookies are enabled.
- [ ] Service-account folder permissions are least privilege.
- [ ] REDCap token is not stored in source or IIS configuration.
- [ ] REDCap connection, push and pull tests pass.
- [ ] Test Country remains temporary and REDCap contains zero Test Country records.
- [ ] Profiling import/comments, blank responses, national counts, and the brief summary are verified.
- [ ] The administrator password remains valid after a supported service restart.
- [ ] Clerk access restrictions are verified.
- [ ] Daily backups run successfully.
- [ ] Off-server encrypted backup exists.
- [ ] Restore test is documented.
- [ ] Application, server and REDCap owners are named.
- [ ] Monitoring and incident contacts are documented.


## Deploying under a subpath

The default deployment uses the domain root. To host at a URL such as
`https://example.org/tools/assessment/`, set `AFRICA_CDC_BASE_PATH=/tools/assessment`
in the server environment before starting the application. For Docker, add this
setting to `docker.env`, rebuild the image, and recreate the application container.
For Windows, set `$env:AFRICA_CDC_BASE_PATH = '/tools/assessment'` in PowerShell
before starting the server, or set it in the service environment and restart.
The setup launcher inherits this environment setting without edits.

Configure the reverse proxy to preserve the prefix when forwarding requests.
For Caddy, use `handle /tools/assessment/*` with `reverse_proxy app:8080` and
forward the exact `/tools/assessment` path as well; avoid `handle_path`, which
strips the prefix. The app redirects the mount URL to its trailing-slash form.
Use `/tools/assessment/health` for manual health checks and
`/tools/assessment/login` for sign-in. Logout redirects within the configured
mount, and session cookies are scoped to it. The Docker health check reads the
same environment setting automatically.

After deployment, verify sign-in, styles and logo, language switching, manual
links, report downloads, and logout at the public subpath. Browser URLs are
relative, so no individual frontend files require changes. Leave the base path
empty for the existing root deployment; root URLs elsewhere in this guide are
examples for that default configuration.
