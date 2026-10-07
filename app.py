"""Cloudera AI Workbench Application entrypoint for the Daedalus Builder."""
from pathlib import Path
import runpy


runpy.run_path(str(Path(__file__).parent / "deploy" / "workbench" / "launch_builder.py"), run_name="__main__")
