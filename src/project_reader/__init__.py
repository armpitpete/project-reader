"""Project Reader foundation package."""

from .assessment import assess_completion, assess_likelihood
from .evidence import PublicEvidenceBundle, collect_public_evidence
from .interpretation import InterpretationBundle, interpret_evidence_bundle
from .models import ProjectReading
from .reading import build_project_reading
from .render import render_html_fragment, render_html_string

__all__ = [
    "InterpretationBundle",
    "ProjectReading",
    "PublicEvidenceBundle",
    "assess_completion",
    "assess_likelihood",
    "build_project_reading",
    "collect_public_evidence",
    "interpret_evidence_bundle",
    "render_html_fragment",
    "render_html_string",
]
