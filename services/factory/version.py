"""Which code a process is running: the Git commit of the checkout it was started from."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def code_revision(root=ROOT):
    """The checked-out commit (12 characters), read from .git without running git; "unknown" outside a checkout."""
    try:
        head = (root / ".git" / "HEAD").read_text().strip()
        if not head.startswith("ref: "):
            return head[:12]
        ref = head[5:]
        loose = root / ".git" / ref
        if loose.is_file():
            return loose.read_text().strip()[:12]
        for line in (root / ".git" / "packed-refs").read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split()[0][:12]
    except OSError:
        pass
    return "unknown"


REVISION = code_revision()
