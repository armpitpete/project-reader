from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.render import render_html

namespace = runpy.run_path(str(ROOT / "examples" / "sample_project.py"))
render_html(namespace["reading"], ROOT / "prototype" / "sample.html")
print("Wrote prototype/sample.html")
