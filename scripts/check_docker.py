"""Smoke-test the built image in an isolated Compose project with dummy secrets.

Run: python scripts/check_docker.py
Requires Docker and Compose >= 2.30; build cdc-surveillance:local first.
Only this script's temporary project and volumes are removed during cleanup.
"""
import http.cookiejar
import io
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
project = "cdc-check-" + uuid.uuid4().hex[:10]


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


with tempfile.TemporaryDirectory(prefix=project) as temp:
    folder = Path(temp)
    # Ephemeral host port; never touch the deployment's real environment file.
    (folder / "compose.yaml").write_text(
        (ROOT / "compose.yaml").read_text().replace("127.0.0.1:8080:8080", "127.0.0.1::8080")
    )
    shutil.copy(ROOT / "compose.https.yaml", folder)
    shutil.copytree(ROOT / "deploy", folder / "deploy")
    (folder / "docker.env").write_text(
        "AFRICA_CDC_REDCAP_API_URL=http://127.0.0.1:9/api/\n"
        "AFRICA_CDC_REDCAP_TOKEN=\n"
        "AFRICA_CDC_SECURE_COOKIES=false\n"
        "AFRICA_CDC_PASSWORD_PEPPER=" + secrets.token_hex(32) + "\n"
    )
    base = ["docker", "compose", "--project-directory", temp, "-p", project,
            "-f", str(folder / "compose.yaml")]

    def compose(*args):
        return run(*base, *args)

    try:
        compose("config", "--quiet")
        run(*base, "-f", str(folder / "compose.https.yaml"), "config", "--quiet")
        compose("up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "90")
        address = "http://" + compose("port", "app", "8080").strip()
        cookies = http.cookiejar.CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

        def request(path, payload=None):
            data = None if payload is None else json.dumps(payload).encode()
            req = urllib.request.Request(address + path, data=data,
                                         headers={"Content-Type": "application/json"})
            with client.open(req, timeout=30) as response:
                return response.read()

        assert json.loads(request("/health"))["status"] == "ok"
        assert b"html" in request("/").lower()
        assert json.loads(request("/api/auth/status"))["setup_required"]
        credentials = {"username": "dockercheck", "password": secrets.token_hex(20) + "Aa1!"}
        assert json.loads(request("/api/auth/setup", credentials))["ok"]
        for endpoint in ("/api/export.xlsx", "/api/report.docx"):
            data = request(endpoint)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                assert archive.testzip() is None
            print("PASS", endpoint, len(data), "bytes")
        compose("exec", "-T", "app", "python", "-c",
                        "import os,pathlib; assert os.getuid()==10001; "
                        "assert not pathlib.Path('/app/.env').exists(); "
                        "assert pathlib.Path('/data/africa_cdc_web.db').exists()")
        compose("up", "-d", "--no-build", "--pull", "never", "--force-recreate", "--wait", "--wait-timeout", "90")
        address = "http://" + compose("port", "app", "8080").strip()
        cookies.clear()
        assert not json.loads(request("/api/auth/status"))["setup_required"]
        assert json.loads(request("/api/auth/login", credentials))["ok"]
        print("PASS Compose validation, health, static assets, account setup, non-root execution,")
        print("     secret exclusion, exports, and account persistence after container replacement")
    except Exception:
        print(compose("logs", "--tail=60", "app"))
        raise
    finally:
        compose("down", "--volumes", "--remove-orphans")
