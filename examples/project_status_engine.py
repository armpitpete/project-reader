from project_reader.assessment import assess_completion, assess_likelihood
from project_reader.models import (
    Claim,
    Evidence,
    EvidenceStrength,
    LikelihoodSignals,
    ProjectReading,
    Technology,
    WorkItem,
    WorkState,
)

HEAD = "d24e979e1747206f0c1ac3c66d3999f479f7ab72"
REPO = "https://github.com/armpitpete/project-status-engine"
README = f"{REPO}/blob/{HEAD}/README.md"

EVIDENCE = (
    Evidence(
        "purpose",
        "README: purpose, source-of-truth rules and completion authority",
        f"{README}#L3-L18",
    ),
    Evidence(
        "outputs",
        "README: public, private and trusted outputs",
        f"{README}#L49-L100",
    ),
    Evidence(
        "validation",
        "README: automated validation, privacy and synchronisation",
        f"{README}#L124-L155",
    ),
    Evidence(
        "completion",
        "README: four authorised stages recorded as 100% complete",
        f"{README}#L194-L208",
    ),
    Evidence(
        "open-issues",
        "GitHub issue search: no open issues",
        f"{REPO}/issues?q=is%3Aissue+is%3Aopen",
    ),
    Evidence(
        "open-prs",
        "GitHub pull request search: no open pull requests",
        f"{REPO}/pulls?q=is%3Apr+is%3Aopen",
    ),
    Evidence(
        "release-commit",
        "Latest main commit: consolidated v1.1 status engine and owner dashboard",
        f"{REPO}/commit/{HEAD}",
    ),
    Evidence(
        "next-inference",
        "Inference from completed authority and empty open-work queues",
        f"{REPO}/issues",
        EvidenceStrength.ESTIMATED,
    ),
)

stages = [
    WorkItem("Activity ranking and dashboard split", WorkState.DONE),
    WorkItem("Authority-backed completion calculation", WorkState.DONE),
    WorkItem("Authenticated private dashboard delivery", WorkState.DONE),
    WorkItem("Daily authority-backed README synchroniser", WorkState.DONE),
]

reading = ProjectReading(
    name="Project Status Engine",
    explanation=Claim(
        "An automatic system that reads GitHub activity and owner-approved progress records, then produces public and private project-status views.",
        ("purpose", "outputs"),
    ),
    status="Complete",
    status_evidence_keys=("completion", "open-issues", "open-prs", "release-commit"),
    completion=assess_completion(
        stages,
        finish_line_defined=True,
        evidence_strength=EvidenceStrength.CONFIRMED,
        evidence_keys=("completion",),
        scope_label="of defined stages",
    ),
    likelihood=assess_likelihood(
        LikelihoodSignals(20, 20, 15, 15, 15, 10, 5, 1.0),
        timeframe="The current defined work has already been reached; no overall project percentage is authorised.",
        already_complete=True,
        evidence_keys=("completion", "open-issues", "open-prs", "release-commit"),
    ),
    done=(
        Claim("It separates recent activity from authority-backed completion.", ("purpose",)),
        Claim("It produces public, private-owner and trusted internal outputs from one scan.", ("outputs",)),
        Claim("It validates generated outputs and protects private repository details.", ("validation",)),
        Claim("All four authorised project stages are recorded as complete.", ("completion",)),
    ),
    remaining=(
        Claim("No unfinished work is currently listed in GitHub issues or pull requests.", ("open-issues", "open-prs")),
        Claim("Any further development would be a new milestone, not unfinished v1.1 work.", ("completion", "next-inference")),
    ),
    next_step=Claim(
        "Decide whether to archive the project as complete or define a new milestone before starting more development.",
        ("completion", "open-issues", "open-prs", "next-inference"),
    ),
    technologies=(
        Technology(
            name="Python",
            simple_explanation="A programming language designed to be readable.",
            use_here="It scans repository data, validates outputs and generates reports.",
            reason_used="The README says validation is implemented once in Python instead of being duplicated in workflow files.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The scripts folder.",
            why_it_matters="One clear implementation is easier to test and less likely to drift.",
            evidence_keys=("validation",),
        ),
        Technology(
            name="GitHub Actions",
            simple_explanation="GitHub's tool for running automatic jobs.",
            use_here="It refreshes status outputs, validates changes and runs the daily synchroniser.",
            reason_used="The project needs status information to update automatically rather than by hand.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The .github/workflows folder.",
            why_it_matters="The owner does not have to maintain a second manual dashboard.",
            evidence_keys=("purpose", "validation"),
        ),
        Technology(
            name="HTML, JSON and Markdown",
            simple_explanation="Three common formats for webpages, structured data and readable documents.",
            use_here="They provide a visual dashboard, machine-readable records and plain reports.",
            reason_used="Different readers and tools need different views of the same verified information.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The generated public, private-build and internal-build folders.",
            why_it_matters="People can read the project while other systems can reuse the same data.",
            evidence_keys=("outputs",),
        ),
    ),
    evidence=EVIDENCE,
    project_url=REPO,
    contact_url="https://github.com/armpitpete",
)
