from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.render import render_html

namespace = runpy.run_path(str(ROOT / "examples" / "project_status_engine.py"))
render_html(namespace["reading"], ROOT / "prototype" / "project-status-engine.html")
print("Wrote prototype/project-status-engine.html")
