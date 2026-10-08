"""Cloudera AI Workbench Application entrypoint for the project-hosted registry PostgreSQL."""
import os
from pathlib import Path
import runpy


LAUNCHER = Path("deploy") / "workbench" / "launch_postgres.py"


def project_root():
    # Workbench runs this script in an IPython kernel: __file__ is undefined and the
    # working directory is the project home, which may be above the repository.
    current = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    candidates = [current, *current.parents]
    if os.getenv("DAEDALUS_ROOT"):
        candidates.insert(0, Path(os.environ["DAEDALUS_ROOT"]))
    candidates += sorted(match.parents[2] for depth in ("*", "*/*") for match in current.glob(f"{depth}/{LAUNCHER}"))
    for candidate in candidates:
        if (candidate / LAUNCHER).is_file():
            return candidate
    raise RuntimeError(f"Cannot find {LAUNCHER} from {current}; set DAEDALUS_ROOT to the Daedalus repository root")


runpy.run_path(str(project_root() / LAUNCHER), run_name="__main__")
