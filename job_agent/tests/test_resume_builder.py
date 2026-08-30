from job_agent.generator.cover_letter_builder import build_cover_letter
from job_agent.generator.resume_builder import build_tailored_resume
from job_agent.models import JobPosting

JOB = JobPosting(
    source="greenhouse",
    external_id="42",
    title="Head of AI",
    company="Acme Health",
    location="Bengaluru, India",
    description=(
        "We need a leader with deep expertise in Agentic AI, Retrieval-Augmented "
        "Generation (RAG), LangChain, and Azure OpenAI to own our AI product roadmap."
    ),
    apply_url="https://example.com/apply",
)


def test_tailored_resume_preserves_facts_and_reorders_skills(profile):
    resume = build_tailored_resume(profile, JOB, max_bullets_per_role=5)

    # No fabrication: name/contact/dates carried through unchanged.
    assert resume["name"] == profile["name"]
    assert resume["email"] == profile["email"]
    assert [r["company"] for r in resume["experience"]] == [r["company"] for r in profile["experience"]]

    # Relevant skill category should be promoted toward the front.
    categories = list(resume["skills"].keys())
    assert categories.index("Generative AI / Agentic AI") <= 2

    # JD keywords the candidate actually has should be picked up.
    assert "Agentic AI" in resume["matched_keywords"] or "LangChain" in resume["matched_keywords"]

    # Bullet selection never invents new bullets.
    original_bullets = {b for role in profile["experience"] for b in role["bullets"]}
    tailored_bullets = {b for role in resume["experience"] for b in role["bullets"]}
    assert tailored_bullets <= original_bullets


def test_bullet_cap_is_respected(profile):
    resume = build_tailored_resume(profile, JOB, max_bullets_per_role=2)
    for role in resume["experience"]:
        assert len(role["bullets"]) <= 2


def test_cover_letter_mentions_company_and_role(profile):
    resume = build_tailored_resume(profile, JOB, max_bullets_per_role=5)
    letter = build_cover_letter(profile, JOB, resume)
    assert JOB.company in letter
    assert JOB.title in letter
    assert profile["email"] in letter
