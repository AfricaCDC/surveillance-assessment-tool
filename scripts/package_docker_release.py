"""Create the Docker source handover using an explicit public-file allowlist."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "Dockerfile", ".dockerignore", "compose.yaml", "compose.https.yaml",
    "compose.local.yaml", "docker.env.example", ".env.example",
    "DOCKER_DEPLOYMENT_GUIDE.md", "REDCAP_WORKSPACE_FIX.md", "CHANGELOG.md",
    "README.md", "USER_MANUAL.md", "requirements.txt", "server.py",
    "surveillance_app.py", "report_builder.py", "recommendation_engine.py",
    "standard_assessment_template.xlsx", "deploy/Caddyfile",
    "scripts/check_docker.py", "scripts/verify_deleted_redcap_workspace.py",
    "scripts/verify_no_local_member_state.py", "scripts/package_docker_release.py",
)


def main():
    files = [ROOT / name for name in FILES]
    files += [path for path in (ROOT / "static").rglob("*") if path.is_file()]
    for path in files:
        if (path.name in {".env", "docker.env"} or ".db" in path.name
                or path.suffix.lower() in {".exe", ".key", ".pem", ".pyc"}
                or "__pycache__" in path.parts):
            raise ValueError(f"Private/runtime file is not allowed: {path.name}")
    archive = ROOT / "cdc-surveillance-docker.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in files:
            package.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(archive) as package:
        assert package.testzip() is None
        assert package.read("server.py") == (ROOT / "server.py").read_bytes()
        assert package.read("static/app.js") == (ROOT / "static/app.js").read_bytes()
    print(f"Verified {archive.name}: {len(files)} files, {archive.stat().st_size} bytes")


if __name__ == "__main__":
    main()
