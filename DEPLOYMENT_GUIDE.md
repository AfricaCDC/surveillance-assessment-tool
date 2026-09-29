# Africa CDC Assessment Web Application

## Production deployment guide

This guide deploys one central copy of the application on Ubuntu Server. Users access it through a domain such as `assessment.africacdc.org`; they do not install separate copies.

For Windows Server, use `WINDOWS_SERVER_DEPLOYMENT_GUIDE.md` in the same project folder.

Give application administrators and data-entry clerks the plain-language `USER_MANUAL.md` after deployment.

Use `APPLICATION_UPDATE_GUIDE.md` for every future production update.

### Production architecture

```text
Users' browsers
      |
      | HTTPS (port 443)
      v
Nginx reverse proxy
      |
      | http://127.0.0.1:8080 (server-local only)
      v
Africa CDC Python application
      |-- SQLite authentication and recovery cache
      `-- HTTPS connection to Africa CDC REDCap API
```

REDCap is the primary assessment-data store. SQLite stores application users, sessions, settings, groups, assignments, and the country index; it does not persist assessment profiles or responses.

### Version 1.0.40 operating rules

- Member State assessment saves require REDCap confirmation; failed saves leave the entered values in the browser for retry.
- The exact country name **Test Country** is temporary in memory, is never written to REDCap, and is discarded on application restart.
- Use a separately approved UAT country name when testing REDCap persistence.
- Profiling imports retain each question's Response and Comments, display immediately, and leave unanswered dropdowns as **No response**.
- Profiling national-coverage totals count only explicit national-level responses; blank and subnational responses are excluded.
- Consolidated recommendations must link each proposed action to a recorded supporting finding.

## 1. Information required from the IT team

Obtain these before starting:

- Ubuntu Server 22.04 LTS or 24.04 LTS.
- A static server IP address.
- A DNS name, recommended: `assessment.africacdc.org`.
- DNS `A` or `AAAA` record pointing that name to the server.
- Inbound ports 80 and 443 allowed to the server.
- Outbound HTTPS access to `tools.africacdc.org`.
- REDCap project API token for PID 932.
- A backup destination accessible only to administrators.

Do not email or include the API token in tickets, screenshots, source code or this guide.

## 2. Prepare Ubuntu

Connect with SSH using an account permitted to run `sudo`, then run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx sqlite3 rsync ufw
```

Create a dedicated service account:

```bash
sudo useradd --system --home /opt/africa-cdc-assessment --shell /usr/sbin/nologin africacdc
sudo mkdir -p /opt/africa-cdc-assessment
sudo mkdir -p /var/lib/africa-cdc-assessment
sudo mkdir -p /var/backups/africa-cdc-assessment
```

## 3. Copy the application to the server

From the administrator's computer, copy the contents of the application folder to a temporary location on the server. Example:

```bash
scp -r "Webapp Surviellance Digital tools assessment" USER@SERVER-IP:/tmp/africa-cdc-assessment
```

On the server, install the application files:

```bash
sudo rsync -a --delete /tmp/africa-cdc-assessment/ /opt/africa-cdc-assessment/
sudo chown -R root:africacdc /opt/africa-cdc-assessment
sudo find /opt/africa-cdc-assessment -type d -exec chmod 750 {} \;
sudo find /opt/africa-cdc-assessment -type f -exec chmod 640 {} \;
```

Do not use `--delete` for later upgrades until the backup step has been completed and the source/target paths have been verified.

## 4. Create the Python environment

```bash
sudo python3 -m venv /opt/africa-cdc-assessment/.venv
sudo /opt/africa-cdc-assessment/.venv/bin/pip install --upgrade pip
sudo /opt/africa-cdc-assessment/.venv/bin/pip install -r /opt/africa-cdc-assessment/requirements.txt
sudo chown -R root:africacdc /opt/africa-cdc-assessment/.venv
```

## 5. Prepare the local authentication and permissions database

For a new installation, the application creates the database automatically. Grant the service account access to the data directory:

```bash
sudo chown africacdc:africacdc /var/lib/africa-cdc-assessment
sudo chmod 700 /var/lib/africa-cdc-assessment
```

To preserve existing administrator and group accounts, copy the existing `africa_cdc_web.db` before starting the service:

```bash
sudo cp /tmp/africa-cdc-assessment/africa_cdc_web.db /var/lib/africa-cdc-assessment/africa_cdc_web.db
sudo chown africacdc:africacdc /var/lib/africa-cdc-assessment/africa_cdc_web.db
sudo chmod 600 /var/lib/africa-cdc-assessment/africa_cdc_web.db
```

Do not copy `-wal` or `-shm` files from a running instance. Stop the old application first or create a consistent SQLite backup.

## 6. Store production settings securely

Create the environment file:

```bash
sudo nano /etc/africa-cdc-assessment.env
```

Enter these values, replacing `PASTE_TOKEN_HERE` locally on the server:

```text
AFRICA_CDC_DB_PATH=/var/lib/africa-cdc-assessment/africa_cdc_web.db
AFRICA_CDC_REDCAP_TOKEN=PASTE_TOKEN_HERE
AFRICA_CDC_SECURE_COOKIES=1
```

Protect the file:

```bash
sudo chown root:root /etc/africa-cdc-assessment.env
sudo chmod 600 /etc/africa-cdc-assessment.env
```

Only root should be able to read this file. The token must never be stored in the application source or Nginx configuration.

## 7. Create the systemd service

Create `/etc/systemd/system/africa-cdc-assessment.service`:

```ini
[Unit]
Description=Africa CDC Surveillance Assessment Web Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=africacdc
Group=africacdc
WorkingDirectory=/opt/africa-cdc-assessment
EnvironmentFile=/etc/africa-cdc-assessment.env
ExecStart=/opt/africa-cdc-assessment/.venv/bin/python /opt/africa-cdc-assessment/server.py --host 127.0.0.1 --port 8080 --no-browser
Restart=on-failure
RestartSec=5
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/africa-cdc-assessment

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now africa-cdc-assessment
sudo systemctl status africa-cdc-assessment --no-pager
curl http://127.0.0.1:8080/health
```

The health response should contain `"status": "ok"`.

If startup fails:

```bash
sudo journalctl -u africa-cdc-assessment -n 100 --no-pager
```

## 8. Configure Nginx

Create `/etc/nginx/sites-available/africa-cdc-assessment`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name assessment.africacdc.org;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
        proxy_send_timeout 180s;
    }
}
```

Enable the site and test the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/africa-cdc-assessment /etc/nginx/sites-enabled/africa-cdc-assessment
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Nginx's official proxy documentation explains `proxy_pass` and forwarded request headers: https://nginx.org/en/docs/http/ngx_http_proxy_module.html

## 9. Configure the firewall

Keep port 8080 private. Only SSH, HTTP and HTTPS should be exposed:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Do not add a public firewall rule for port 8080.

## 10. Enable HTTPS

Confirm that DNS already points `assessment.africacdc.org` to the server. Then follow the current Certbot instructions for Ubuntu and Nginx at:

https://certbot.eff.org/instructions?ws=nginx&os=snap

Typical commands are:

```bash
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/local/bin/certbot
sudo certbot --nginx -d assessment.africacdc.org
sudo certbot renew --dry-run
```

Choose the option that redirects HTTP to HTTPS. Certbot's official instructions explain certificate installation and renewal testing: https://certbot.eff.org/instructions?ws=nginx&os=snap

## 11. Verify the deployed application

Open:

```text
https://assessment.africacdc.org/login
```

Complete this checklist:

1. The login page appears first.
2. The browser shows a valid HTTPS padlock.
3. The administrator can sign in.
4. The Inventory, Profiling, Gap Analysis and Output screens open.
5. Existing country assessments appear.
6. Under REDCap, the API URL is `https://tools.africacdc.org/africacdcrc/api/`.
7. **Test connection** succeeds.
8. Saving an approved persistent UAT country succeeds.
9. The matching `acdc-N` record appears in REDCap; a separate **Test Country** check creates no REDCap record.
10. **Load current country from REDCap** restores the same tool/profile/response counts.
11. A clerk account sees only its assigned phase and items.
12. Logging out returns to the login screen.

## 12. Configure backups

REDCap contains the assessment data. The local database contains login accounts, permissions, groups, assignments, and configuration. Back it up daily.

Create `/usr/local/sbin/backup-africa-cdc-assessment`:

```bash
#!/usr/bin/env bash
set -euo pipefail
backup_dir=/var/backups/africa-cdc-assessment
stamp=$(date -u +%Y%m%dT%H%M%SZ)
install -d -m 700 "$backup_dir"
sqlite3 /var/lib/africa-cdc-assessment/africa_cdc_web.db ".backup '$backup_dir/africa_cdc_web_$stamp.db'"
find "$backup_dir" -type f -name 'africa_cdc_web_*.db' -mtime +30 -delete
```

Protect and schedule it:

```bash
sudo chown root:root /usr/local/sbin/backup-africa-cdc-assessment
sudo chmod 700 /usr/local/sbin/backup-africa-cdc-assessment
sudo crontab -e
```

Add:

```cron
15 1 * * * /usr/local/sbin/backup-africa-cdc-assessment
```

Test the backup and restore procedure before production launch. Store an additional encrypted copy outside the application server according to Africa CDC policy.

## 13. Updating the application

Before every update:

```bash
sudo /usr/local/sbin/backup-africa-cdc-assessment
sudo systemctl stop africa-cdc-assessment
```

Copy the new application files to `/opt/africa-cdc-assessment`, but do not overwrite:

- `/etc/africa-cdc-assessment.env`
- `/var/lib/africa-cdc-assessment/africa_cdc_web.db`
- `/var/backups/africa-cdc-assessment/`

Then run:

```bash
sudo /opt/africa-cdc-assessment/.venv/bin/pip install -r /opt/africa-cdc-assessment/requirements.txt
sudo chown -R root:africacdc /opt/africa-cdc-assessment
sudo systemctl start africa-cdc-assessment
sudo systemctl status africa-cdc-assessment --no-pager
curl http://127.0.0.1:8080/health
```

## 14. Operational responsibilities

### Application administrator

- Creates countries and working groups.
- Assigns tools and domains.
- Manages clerk credentials.
- Checks REDCap synchronization status.
- Reviews assessment completeness.

### Server/IT administrator

- Maintains Ubuntu, DNS, Nginx and HTTPS.
- Protects and rotates the REDCap token.
- Monitors the service and storage.
- Tests backups and restores.
- Applies security and application updates.

### REDCap system administrator

- Maintains PID 932 and its API permissions.
- Maintains the REDCap API endpoint.
- Reviews REDCap audit logs and project access.

## 15. Troubleshooting

### Website does not open

```bash
sudo systemctl status nginx --no-pager
sudo systemctl status africa-cdc-assessment --no-pager
curl http://127.0.0.1:8080/health
```

### HTTP 502 Bad Gateway

The Python service is normally stopped or unhealthy:

```bash
sudo journalctl -u africa-cdc-assessment -n 100 --no-pager
```

### REDCap connection fails

- Confirm outbound HTTPS access to `tools.africacdc.org`.
- Confirm the API URL is exactly `https://tools.africacdc.org/africacdcrc/api/`.
- Confirm the token belongs to PID 932 and retains API import/export permissions.
- Ask the REDCap system administrator whether the token was revoked or rotated.

### REDCap save fails

- Keep the browser page open; entered values remain available there for retry.
- Restore REDCap connectivity and repeat the save.
- Verify the matching record in REDCap before leaving the assessment.
- Do not treat **Test Country: temporary only - not saved to REDCap** as a failure; this is the required non-production behaviour.

### Token rotation

1. Generate/approve the replacement token in REDCap.
2. Update `AFRICA_CDC_REDCAP_TOKEN` in `/etc/africa-cdc-assessment.env`.
3. Run `sudo systemctl restart africa-cdc-assessment`.
4. Test REDCap connectivity with an approved persistent UAT record. Do not use the reserved **Test Country** name.

## Final production handover checklist

- [ ] One central server instance only.
- [ ] DNS resolves correctly.
- [ ] HTTPS is valid and HTTP redirects to HTTPS.
- [ ] Port 8080 is not publicly exposed.
- [ ] Secure cookies are enabled.
- [ ] Environment file permissions are `600`.
- [ ] REDCap connection, push and pull tests pass.
- [ ] Test Country remains temporary and REDCap contains zero Test Country records.
- [ ] Standard Profiling import, comments, blank responses, national counts, and brief summary are verified.
- [ ] Evidence-linked recommendation analysis completes without truncation.
- [ ] Clerk permissions are verified.
- [ ] Daily backups run successfully.
- [ ] Restore test is documented.
- [ ] IT and application owners are named.
- [ ] Monitoring and incident contacts are documented.
