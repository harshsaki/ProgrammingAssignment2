"""Builds a tailored cover letter as plain text paragraphs.

Deterministic, template-based baseline -- always available even with no
network/API access. If generation.use_llm_enhancement is on and an
ANTHROPIC_API_KEY is present, llm_enhance.polish_cover_letter() rewrites
this into more natural prose while keeping every fact.
"""

from __future__ import annotations

from ..models import JobPosting


def build_cover_letter(profile: dict, job: JobPosting, tailored_resume: dict) -> str:
    top_role = tailored_resume["experience"][0]
    top_bullets = top_role["bullets"][:2]
    matched = tailored_resume.get("matched_keywords", [])[:4]

    greeting = f"Dear {job.company} Hiring Team,"

    para1 = (
        f"I'm writing to apply for the {job.title} position at {job.company}. "
        f"I'm a {profile['headline'].split('|')[0].strip()} with {profile['years_experience']}+ years "
        f"building and scaling enterprise AI and Generative AI systems, most recently as "
        f"{top_role['title']} at {top_role['company']}."
    )

    achievement_lines = "\n".join(f"- {b}" for b in top_bullets)
    para2 = (
        "A few things from that experience I believe are directly relevant to this role:\n"
        f"{achievement_lines}"
    )

    if matched:
        para3 = (
            f"Your posting highlights {', '.join(matched)} -- these map closely to my day-to-day work, "
            "and I'd welcome the chance to bring that same depth to your team."
        )
    else:
        para3 = (
            "I'd welcome the opportunity to bring this same combination of AI engineering depth and "
            "product ownership to your team."
        )

    closing = (
        f"Thank you for your consideration. I've attached my resume and would be glad to discuss "
        f"how I can contribute to {job.company}'s AI roadmap.\n\nBest regards,\n{profile['name']}\n"
        f"{profile['phone']} | {profile['email']} | {profile['linkedin']}"
    )

    return "\n\n".join([greeting, para1, para2, para3, closing])
