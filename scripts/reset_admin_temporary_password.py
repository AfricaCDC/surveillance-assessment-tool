"""Generate a temporary administrator password for local account recovery."""

import sys
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import server  # noqa: E402


temporary_password = server.generated_password()
with server._disk_connect() as db:
    account = db.execute("SELECT id,username FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if not account:
        raise SystemExit("No administrator account exists")
    db.execute(
        "UPDATE users SET password_hash=?,active=1,last_login_at=NULL WHERE id=?",
        (server.password_digest(temporary_password), account["id"]),
    )
    db.execute("DELETE FROM sessions WHERE user_id=?", (account["id"],))

print(f"USERNAME={account['username']}")
print(f"TEMPORARY_PASSWORD={temporary_password}")
