# Docker deployment on Ubuntu 24.04

This packages the current Python web app. SQLite accounts/settings persist in a
Docker volume; Member State assessment data still saves directly to REDCap.
Docker does not resolve SSH login failures: first obtain working SSH and sudo
access from IT. Commands below are for Ubuntu unless labelled Windows.

Local validation: the Linux image built successfully. An isolated Compose test
passed health/login, administrator creation, Excel and Word exports, non-root
execution, and account persistence after replacing the container. Live REDCap
and your VM's domain/certificate still require deployment-time verification.
To repeat the isolated checks after building: `python scripts/check_docker.py`.

## 1. Install Docker on the VM

If Docker is already installed, check `sudo docker version` and
`sudo docker compose version` first. Compose 2.30 or later is required.
For a fresh VM, follow the official repository installation instructions:
https://docs.docker.com/engine/install/ubuntu/
Install Docker Engine, Buildx, and the Compose plugin. Do not remove existing
container software without checking with IT. Then run:

```bash
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker compose version
mkdir -p ~/cdc-surveillance
```

## 2. Transfer the deployment package

From Windows PowerShell in this project folder (replace USERNAME and VM_IP):

```powershell
scp .\cdc-surveillance-docker.zip USERNAME@VM_IP:~/
```

Back in Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y unzip
unzip ~/cdc-surveillance-docker.zip -d ~/cdc-surveillance
cd ~/cdc-surveillance
```

The zip contains source, static assets, Docker configuration, and a sample
environment file. It excludes real secrets, local databases, and Windows builds.

## 3. Configure the application

For a new installation:

```bash
umask 077
cp -n docker.env.example docker.env
chmod 600 docker.env
openssl rand -base64 32
nano docker.env
```

Put your actual REDCap token and the generated password pepper into docker.env.
Store the pepper separately in the organisation's secret manager. Use literal
values without surrounding quotes; raw env-file parsing preserves dollar signs.
Do not paste tokens or the pepper into chat or tickets. Do not run a plain
`docker compose config` for sharing: it can display secrets. Use `config --quiet`.

If keeping existing accounts, use their existing pepper instead of generating a
replacement, and migrate the database using step 7 BEFORE first startup.
The local desktop .env is deliberately not included in the image or mounted.
Container configuration comes from docker.env, with Compose fixing the database
path to /data and disabling background REDCap synchronization.

Ollama is optional and is not installed by this package. On the 4 GB VM, start
with the app alone and its built-in report assistant fallback. A configured
Ollama URL must be reachable from inside the container; 127.0.0.1 is the container.

## 4. Start privately and create the administrator

```bash
sudo docker compose config --quiet
sudo docker compose up -d --build --wait
sudo docker compose ps
curl --fail http://127.0.0.1:8080/health
```

Expected health response contains `"status": "ok"`. This checks the application,
not REDCap connectivity. If startup fails:

```bash
sudo docker compose logs --tail=100 app
```

Only the VM itself can access port 8080. In a separate Windows PowerShell window,
open an SSH tunnel and leave it running:

```powershell
ssh -N -L 18080:127.0.0.1:8080 USERNAME@VM_IP
```

Open http://127.0.0.1:18080 on Windows. Create the administrator account before
public access is enabled. Check login, forms, and report exports using Test
Country. Test Country is temporary and disappears on restart; to verify REDCap
persistence, use an IT-approved UAT country/project and confirm a saved record
can be reloaded after restarting the container.

## 5. Enable HTTPS

Ask IT for the actual public DNS name, DNS records pointing to this VM (or its
forwarding gateway), and inbound TCP ports 80 and 443. Keep management SSH
restricted to authorised networks. Docker-published ports can bypass UFW rules;
have IT enforce the intended exposure at the network firewall/Docker layer.
Do not publish port 8080 externally.

For an internet-accessible domain, edit deploy/Caddyfile and replace
assessment.example.org with your actual domain, without https://. Then:

```bash
sudo docker compose -f compose.yaml -f compose.https.yaml config --quiet
sudo docker compose -f compose.yaml -f compose.https.yaml up -d --build --wait
sudo docker compose -f compose.yaml -f compose.https.yaml logs --tail=100 proxy
```

Open https://YOUR_DOMAIN and check login and reports. Caddy obtains and renews
certificates, redirects HTTP to HTTPS, and proxies requests to the app. Its
certificate state persists in separate volumes. The HTTPS override enables
secure session cookies; use the HTTPS address thereafter.

If access is VPN/internal only, or IT already supplies an HTTPS gateway, ask IT
to terminate TLS at that gateway instead of starting this public Caddy setup.
Set AFRICA_CDC_SECURE_COOKIES=true in docker.env and recreate the app. A gateway
on the same VM can proxy to 127.0.0.1:8080; a gateway on another host requires a
separately agreed private binding and firewall configuration.

References: https://caddyserver.com/docs/automatic-https and
https://docs.docker.com/reference/compose-file/services/

## 6. Operations and backups

After enabling bundled HTTPS, always include both Compose files for updates:

```bash
sudo docker compose -f compose.yaml -f compose.https.yaml up -d --build --wait
sudo docker compose -f compose.yaml -f compose.https.yaml ps
```

Restart policies start containers after a VM/Docker reboot. Health checks report
failure but do not automatically restart a running unhealthy process; configure
IT monitoring for the health endpoint and container state. Run one app instance;
the app uses in-memory assessment workspaces and a single SQLite account store.

Before updating, back up the accounts/settings database to an access-controlled,
encrypted backup destination. Choose an actual approved path in place of
/APPROVED_BACKUP_DIRECTORY, then use a unique filename:

```bash
sudo docker compose stop app
sudo docker compose cp app:/data/africa_cdc_web.db /APPROVED_BACKUP_DIRECTORY/accounts-YYYYMMDD-HHMM.db
sudo docker compose start app
```

Confirm the copy succeeded before updating. Store docker.env secrets separately
through the approved secret-management process. REDCap needs its own managed
backup; this SQLite copy does not contain the Member State assessments. Test
restoration in an isolated deployment before relying on a backup.

`docker compose down` retains named volumes. Never use `down --volumes` or delete
the app_data volume unless you intend to erase the stored accounts/settings.

## 7. Optional account migration before first startup

Stop the old app before copying its SQLite database, or obtain a consistent
SQLite backup. Transfer that file securely as accounts-migration.db to this
deployment directory and preserve the original password pepper in docker.env.
Do this only against a NEW, empty Docker volume, not over an existing deployment:

```bash
sudo docker compose build
sudo docker compose create app
sudo docker compose cp ./accounts-migration.db app:/data/africa_cdc_web.db
sudo docker compose run --rm --no-deps --user 0 app python -c "import os; p='/data/africa_cdc_web.db'; os.chown(p,10001,10001); os.chmod(p,0o600)"
sudo docker compose up -d --wait
```

Verify existing login and assignments before retiring the old installation.
Remove temporary migration copies according to the organisation's data policy.


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
