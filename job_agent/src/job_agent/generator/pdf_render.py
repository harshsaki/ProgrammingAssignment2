"""Renders tailored resume/cover letter dicts to ATS-friendly PDFs.

Kept deliberately plain: single column, standard fonts, no tables/text
boxes/graphics. Fancy multi-column resume templates are the single most
common reason ATS parsers mangle a resume into unreadable text -- plain
beats pretty here.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

_STYLES = getSampleStyleSheet()

_NAME_STYLE = ParagraphStyle("Name", parent=_STYLES["Title"], fontSize=18, spaceAfter=2)
_CONTACT_STYLE = ParagraphStyle("Contact", parent=_STYLES["Normal"], fontSize=9, spaceAfter=10)
_SECTION_STYLE = ParagraphStyle(
    "Section", parent=_STYLES["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=4,
    textColor="#1a1a1a",
)
_ROLE_STYLE = ParagraphStyle("Role", parent=_STYLES["Normal"], fontSize=10, spaceAfter=1, leading=13)
_BULLET_STYLE = ParagraphStyle("Bullet", parent=_STYLES["Normal"], fontSize=9.5, leading=13)
_BODY_STYLE = ParagraphStyle("Body", parent=_STYLES["Normal"], fontSize=9.5, leading=14, spaceAfter=8)


def render_resume_pdf(resume: dict, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=LETTER,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    story = [
        Paragraph(resume["name"], _NAME_STYLE),
        Paragraph(resume["headline"], _CONTACT_STYLE),
        Paragraph(
            f"{resume['location']} | {resume['phone']} | {resume['email']} | {resume['linkedin']}",
            _CONTACT_STYLE,
        ),
        Paragraph("PROFESSIONAL SUMMARY", _SECTION_STYLE),
        Paragraph(resume["summary"], _BODY_STYLE),
        Paragraph("CORE SKILLS", _SECTION_STYLE),
    ]
    for category, items in resume["skills"].items():
        story.append(Paragraph(f"<b>{category}:</b> {', '.join(items)}", _BODY_STYLE))

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", _SECTION_STYLE))
    for role in resume["experience"]:
        story.append(
            Paragraph(f"<b>{role['company']} — {role['title']}</b>", _ROLE_STYLE)
        )
        story.append(
            Paragraph(f"{role['start']} – {role['end']} | {role['location']}", _BULLET_STYLE)
        )
        story.append(
            ListFlowable(
                [ListItem(Paragraph(b, _BULLET_STYLE)) for b in role["bullets"]],
                bulletType="bullet", start="•", leftIndent=14,
            )
        )
        story.append(Spacer(1, 6))

    if resume.get("projects"):
        story.append(Paragraph("SELECTED AI PROJECTS", _SECTION_STYLE))
        story.append(Paragraph(" | ".join(resume["projects"]), _BODY_STYLE))

    if resume.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", _SECTION_STYLE))
        story.append(Paragraph(" | ".join(resume["certifications"]), _BODY_STYLE))

    if resume.get("honors"):
        story.append(Paragraph("HONORS & AWARDS", _SECTION_STYLE))
        story.append(Paragraph(" | ".join(resume["honors"]), _BODY_STYLE))

    if resume.get("education"):
        story.append(Paragraph("EDUCATION", _SECTION_STYLE))
        for edu in resume["education"]:
            story.append(
                Paragraph(f"{edu['degree']} — {edu['school']} ({edu['start']} – {edu['end']})", _BODY_STYLE)
            )

    if resume.get("languages"):
        story.append(Paragraph("LANGUAGES", _SECTION_STYLE))
        story.append(Paragraph(" | ".join(resume["languages"]), _BODY_STYLE))

    doc.build(story)
    return out_path


def render_cover_letter_pdf(cover_letter_text: str, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=LETTER,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    story = []
    for para in cover_letter_text.split("\n\n"):
        text_html = para.replace("\n", "<br/>")
        story.append(Paragraph(text_html, _BODY_STYLE))
    doc.build(story)
    return out_path
