from project_reader.assessment import assess_completion, assess_likelihood
from project_reader.models import (
    Claim,
    EvidenceStrength,
    LikelihoodSignals,
    ProjectReading,
    Technology,
    WorkItem,
    WorkState,
)

work = [
    WorkItem("Purpose and first-screen contract", WorkState.DONE, 2),
    WorkItem("Completion assessment", WorkState.DONE, 2),
    WorkItem("Likelihood assessment", WorkState.DONE, 2),
    WorkItem("Repository ingestion", WorkState.IN_PROGRESS, 2),
    WorkItem("Evidence-backed interpretation", WorkState.TODO, 3),
    WorkItem("Accessible live reader", WorkState.TODO, 2),
]

reading = ProjectReading(
    name="Project Reader",
    explanation=Claim(
        "A simple and educational way to understand what a GitHub project is, how far it has progressed, and what remains."
    ),
    status="Active",
    status_evidence_keys=(),
    completion=assess_completion(
        work,
        finish_line_defined=True,
        evidence_strength=EvidenceStrength.CONFIRMED,
    ),
    likelihood=assess_likelihood(
        LikelihoodSignals(
            finish_line_clarity=18,
            recent_progress=18,
            bounded_remaining_work=12,
            next_step_clarity=15,
            manageable_blockers=11,
            delivery_history=6,
            repository_health=4,
            evidence_coverage=0.75,
        ),
        timeframe="Foundation milestone within 90 days",
    ),
    done=(
        Claim("The simple first-screen questions are agreed."),
        Claim("Completion and likelihood are measured separately."),
        Claim("The educational technology-card format is defined."),
    ),
    remaining=(
        Claim("Read a real public repository."),
        Claim("Connect every important answer to evidence."),
        Claim("Test the page with a non-technical reader lens."),
    ),
    next_step=Claim("Use one public repository to prove the full five-question reading flow."),
    technologies=(
        Technology(
            name="Python",
            simple_explanation="A language used to give computers clear instructions.",
            use_here="It calculates project scores and prepares the project reading.",
            reason_used="It is readable, widely supported, and works directly with Gitingest.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The src/project_reader folder.",
            why_it_matters="Readable code makes the scoring rules easier to inspect and challenge.",
        ),
        Technology(
            name="Gitingest",
            simple_explanation="A tool that gathers useful information from a Git repository.",
            use_here="It collects the repository structure and readable file contents.",
            reason_used="It avoids rebuilding reliable repository extraction from scratch.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The repository-ingestion layer.",
            why_it_matters="Project Reader can focus on meaning, evidence, and accessibility.",
        ),
        Technology(
            name="HTML and CSS",
            simple_explanation="The standard building blocks for webpage content and appearance.",
            use_here="They display the simple project page.",
            reason_used="They create a fast, accessible proof without a large frontend framework.",
            reason_strength=EvidenceStrength.CONFIRMED,
            location="The HTML renderer and generated prototype.",
            why_it_matters="A small page is easier to load, understand, test, and maintain.",
        ),
    ),
    project_url="https://github.com/armpitpete/project-reader",
    contact_url="https://github.com/armpitpete",
)
