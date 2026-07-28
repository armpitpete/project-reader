from pathlib import Path
import runpy

from project_reader.render import render_html

namespace = runpy.run_path("examples/sample_project.py")
render_html(namespace["reading"], Path("prototype/sample.html"))
print("Wrote prototype/sample.html")
