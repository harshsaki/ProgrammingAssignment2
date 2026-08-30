import tempfile
from pathlib import Path

from job_agent.generator.cover_letter_builder import build_cover_letter
from job_agent.generator.pdf_render import render_cover_letter_pdf, render_resume_pdf
from job_agent.generator.resume_builder import build_tailored_resume
from job_agent.models import JobPosting

JOB = JobPosting(
    source="lever", external_id="7", title="AI Product Owner", company="Beta Corp",
    location="Bengaluru, India", description="Own our RAG and Agentic AI product roadmap.",
    apply_url="https://example.com/apply",
)


def test_resume_and_cover_letter_render_to_valid_pdfs(profile):
    resume = build_tailored_resume(profile, JOB, max_bullets_per_role=4)
    letter = build_cover_letter(profile, JOB, resume)

    with tempfile.TemporaryDirectory() as tmp:
        resume_path = render_resume_pdf(resume, Path(tmp) / "resume.pdf")
        letter_path = render_cover_letter_pdf(letter, Path(tmp) / "cover_letter.pdf")

        assert resume_path.exists() and resume_path.stat().st_size > 0
        assert letter_path.exists() and letter_path.stat().st_size > 0
        assert resume_path.read_bytes()[:4] == b"%PDF"
        assert letter_path.read_bytes()[:4] == b"%PDF"
