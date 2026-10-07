"""Create local-only development credentials without overwriting existing values."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    print(".env already exists; keeping your configuration.")
else:
    lines = []
    for line in (root / ".env.example").read_text().splitlines():
        if "=replace-with-" in line:
            line = line.split("=", 1)[0] + "=" + secrets.token_hex(24)
        lines.append(line)
    path.touch(mode=0o600, exist_ok=False)
    path.write_text("\n".join(lines) + "\n")
    print("Created .env with random local credentials (gitignored).")
print("Start: docker compose up --build -d")
print("Builder: http://localhost:5173")
print("Use FACTORY_ADMINISTRATOR_TOKEN from .env to sign in.")
