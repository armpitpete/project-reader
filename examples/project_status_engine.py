from project_reader.assessment import assess_completion, assess_likelihood
from project_reader.models import (
    Claim,
    Evidence,
    EvidenceStrength,
    LikelihoodSignals,
    ProjectReading,
    RepositoryLanguage,
    Technology,
    WorkItem,
    WorkState,
)

HEAD = "d24e979e1747206f0c1ac3c66d3999f479f7ab72"
REPO = "https://github.com/armpitpete/project-status-engine"
README = f"{REPO}/blob/{HEAD}/README.md"
PROGRESS = f"{REPO}/blob/{HEAD}/.project/progress.json"
LANGUAGES = f"https://api.github.com/repos/armpitpete/project-status-engine/languages"
CHECKED_AT = "28 July 2026 at 12:02 BST"

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
        ".project/progress.json: four authorised stages complete; overall percentage disabled",
        PROGRESS,
    ),
    Evidence(
        "open-issues",
        f"GitHub issue search checked {CHECKED_AT}: no open issues",
        f"{REPO}/issues?q=is%3Aissue+is%3Aopen",
    ),
    Evidence(
        "open-prs",
        f"GitHub pull request search checked {CHECKED_AT}: no open pull requests",
        f"{REPO}/pulls?q=is%3Apr+is%3Aopen",
    ),
    Evidence(
        "release-commit",
        "Source commit used for this reading: consolidated v1.1 status engine and owner dashboard",
        f"{REPO}/commit/{HEAD}",
    ),
    Evidence(
        "language:python",
        "Repository languages: Python (74.7%)",
        LANGUAGES,
    ),
    Evidence(
        "language:sourcepawn",
        "Repository languages: SourcePawn (11.6%)",
        LANGUAGES,
    ),
    Evidence(
        "language:c-plus-plus",
        "Repository languages: C++ (8.6%)",
        LANGUAGES,
    ),
    Evidence(
        "language:pawn",
        "Repository languages: Pawn (2.3%)",
        LANGUAGES,
    ),
    Evidence(
        "language:shell",
        "Repository languages: Shell (1.8%)",
        LANGUAGES,
    ),
    Evidence(
        "language:powershell",
        "Repository languages: PowerShell (1%)",
        LANGUAGES,
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
        "An automatic system that reads GitHub activity and approved progress records, then produces public and private project-status views.",
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
        Claim("It separates recent activity from approved completion records.", ("purpose",)),
        Claim("It produces public, private-owner and trusted internal outputs from one scan.", ("outputs",)),
        Claim("It validates generated outputs and protects private repository details.", ("validation",)),
        Claim("All four planned parts are recorded as finished.", ("completion",)),
    ),
    remaining=(),
    remaining_empty=Claim("Nothing currently listed.", ("open-issues", "open-prs")),
    next_step=Claim(
        "Decide whether to archive the project as complete or define a new milestone before starting more development.",
        ("completion", "open-issues", "open-prs", "next-inference"),
    ),
    repository_languages=(
        RepositoryLanguage("Python", 74.7, 256862, ("language:python",)),
        RepositoryLanguage("SourcePawn", 11.6, 39847, ("language:sourcepawn",)),
        RepositoryLanguage("C++", 8.6, 29503, ("language:c-plus-plus",)),
        RepositoryLanguage("Pawn", 2.3, 7835, ("language:pawn",)),
        RepositoryLanguage("Shell", 1.8, 6272, ("language:shell",)),
        RepositoryLanguage("PowerShell", 1.0, 3603, ("language:powershell",)),
    ),
    technologies=(
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
    source_commit=HEAD,
    assessed_at=CHECKED_AT,
    open_work_checked_at=CHECKED_AT,
    project_url=REPO,
    contact_url="https://github.com/armpitpete",
)
