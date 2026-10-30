"""Smoke-test the Windows executable with isolated settings and storage."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", nargs="?", default=str(ROOT / "package_dist/AfricaCDCWebAssessment.exe"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="assessment_exe_check_", ignore_cleanup_errors=True) as temporary:
        folder = Path(temporary)
        executable = folder / "AfricaCDCWebAssessment.exe"
        shutil.copy2(args.executable, executable)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        environment = {key: value for key, value in os.environ.items() if not key.startswith("AFRICA_CDC_")}
        environment.update(AFRICA_CDC_DB_PATH=str(folder / "test.db"),
                           AFRICA_CDC_PASSWORD_PEPPER=secrets.token_hex(32),
                           AFRICA_CDC_REDCAP_API_URL="https://example.invalid/api/",
                           AFRICA_CDC_REDCAP_TOKEN="")
        with (folder / "process.log").open("w") as log:
            process = subprocess.Popen([str(executable), "--host", "127.0.0.1", "--port", str(port), "--no-browser"],
                                       cwd=folder, env=environment, stdout=log, stderr=log,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                address = f"http://127.0.0.1:{port}"
                for _ in range(90):
                    if process.poll() is not None:
                        raise RuntimeError("Executable exited before startup")
                    try:
                        with urlopen(address + "/health", timeout=1) as response:
                            health = json.load(response)
                        break
                    except OSError:
                        time.sleep(0.5)
                else:
                    raise RuntimeError("Executable startup timed out")
                assert health["status"] == "ok" and health["app_version"] == "1.0.43", health
                with urlopen(address + "/app.js") as response:
                    assert response.read() == (ROOT / "static/app.js").read_bytes()
                with urlopen(address + "/api/auth/status") as response:
                    assert json.load(response)["setup_required"]
                print("PASS executable: v1.0.43 health, bundled updated JavaScript, isolated fresh database")
            finally:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else:
                    process.terminate()
                process.wait(timeout=20)


if __name__ == "__main__":
    main()
