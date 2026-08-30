"""Wires everything together: search -> dedup -> match -> generate -> apply.

Run via `python -m job_agent.cli run`. Designed to be re-run repeatedly
(e.g. daily via cron/a scheduled trigger) -- SeenJobsStore means each run
only processes postings it hasn't handled before.
"""

from __future__ import annotations

import time
from pathlib import Path

from .apply.base import ApplyEngine
from .apply.greenhouse_apply import GreenhouseApplyEngine
from .apply.lever_apply import LeverApplyEngine
from .apply.manual_stage import ManualStageEngine
from .apply.safety import ApplyGuard
from .config import load_config, load_profile
from .generator import llm_enhance
from .generator.cover_letter_builder import build_cover_letter
from .generator.pdf_render import render_cover_letter_pdf, render_resume_pdf
from .generator.resume_builder import build_tailored_resume
from .matching import MatchConfig, rank_jobs
from .models import GeneratedApplication
from .sources.greenhouse import GreenhouseSource
from .sources.indeed_import import IndeedImportSource
from .sources.lever import LeverSource
from .sources.linkedin_import import LinkedInImportSource
from .storage import ApplicationsLog, SeenJobsStore


def build_sources(cfg: dict, base_dir: Path) -> list:
    sources = []
    s = cfg["sources"]
    country = cfg["search"]["country"]

    if s["greenhouse"]["enabled"] and s["greenhouse"]["boards"]:
        sources.append(GreenhouseSource(s["greenhouse"]["boards"], country_filter=country))
    if s["lever"]["enabled"] and s["lever"]["boards"]:
        sources.append(LeverSource(s["lever"]["boards"], country_filter=country))
    if s["indeed"]["enabled"]:
        sources.append(IndeedImportSource(base_dir / s["indeed"]["import_file"]))
    if s["linkedin"]["enabled"]:
        sources.append(LinkedInImportSource(base_dir / s["linkedin"]["import_file"]))
    return sources


def build_applicant_info(profile: dict) -> dict:
    parts = profile["name"].split()
    first, last = parts[0], " ".join(parts[1:]) or parts[0]
    return {
        "first_name": first,
        "last_name": last,
        "full_name": profile["name"],
        "email": profile["email"],
        "phone": profile["phone"],
    }


def choose_apply_engine(
    source: str, guard: ApplyGuard, applicant: dict, outbox_dir: Path, headless: bool = True
) -> tuple[ApplyEngine, bool]:
    """Returns (engine, is_auto_submit_capable)."""
    if source == "greenhouse":
        return GreenhouseApplyEngine(applicant, headless=headless), True
    if source == "lever":
        return LeverApplyEngine(applicant, headless=headless), True
    return ManualStageEngine(outbox_dir), False


def run(config_path: str | Path, base_dir: str | Path | None = None) -> list:
    base_dir = Path(base_dir) if base_dir else Path(config_path).resolve().parent.parent
    cfg = load_config(config_path)
    profile = load_profile(base_dir / "profile" / "profile.json")

    outbox_dir = base_dir / cfg["output"]["outbox_dir"]
    seen_store = SeenJobsStore(base_dir / cfg["output"]["seen_jobs_db"])
    log = ApplicationsLog(base_dir / cfg["output"]["applications_log"])
    guard = ApplyGuard(
        log=log,
        auto_submit_sources=cfg["apply"]["auto_submit_sources"],
        max_applications_per_day=cfg["apply"]["max_applications_per_day"],
        dry_run=cfg["apply"]["dry_run"],
    )
    applicant = build_applicant_info(profile)

    match_cfg = MatchConfig(
        target_titles=cfg["search"]["titles"],
        keywords_any=cfg["search"]["keywords_any"],
        min_years_experience=cfg["search"]["min_years_experience"],
        min_match_score=cfg["search"]["min_match_score"],
        country=cfg["search"]["country"],
    )

    all_jobs = []
    for source in build_sources(cfg, base_dir):
        all_jobs.extend(source.search())

    new_jobs = [j for j in all_jobs if not seen_store.has_seen(j.dedup_key)]
    matches = rank_jobs(new_jobs, profile, match_cfg)

    apply_mode = cfg["apply"]["mode"]
    dry_run = cfg["apply"]["dry_run"]
    cooldown = cfg["apply"]["cooldown_seconds_between_applications"]
    max_bullets = cfg["generation"]["max_resume_bullets_per_role"]
    use_llm = cfg["generation"]["use_llm_enhancement"]
    llm_model = cfg["generation"]["llm_model"]

    records = []
    for match in matches:
        job = match.job
        tailored_resume = build_tailored_resume(profile, job, max_bullets_per_role=max_bullets)
        cover_letter_text = build_cover_letter(profile, job, tailored_resume)

        if use_llm:
            tailored_resume["summary"] = llm_enhance.polish_summary(tailored_resume["summary"], model=llm_model)
            cover_letter_text = llm_enhance.polish_cover_letter(cover_letter_text, model=llm_model)

        work_dir = base_dir / ".generated" / job.dedup_key.replace(":", "_").replace("/", "_")
        resume_pdf = render_resume_pdf(tailored_resume, work_dir / "resume.pdf")
        cover_pdf = render_cover_letter_pdf(cover_letter_text, work_dir / "cover_letter.pdf")

        application = GeneratedApplication(
            job=job, match=match,
            resume_pdf_path=str(resume_pdf), cover_letter_pdf_path=str(cover_pdf),
            tailored_summary=tailored_resume["summary"],
        )

        auto_ok, reason = (False, "apply.mode is stage_only")
        if apply_mode == "auto":
            auto_ok, reason = guard.can_auto_submit(job)

        if auto_ok:
            engine, _ = choose_apply_engine(job.source, guard, applicant, outbox_dir)
        else:
            engine = ManualStageEngine(outbox_dir)

        record = engine.submit(application, dry_run=dry_run)
        if not auto_ok and record.status == "staged":
            record.detail = f"{record.detail} (auto-submit not used: {reason})"

        log.append(record)
        seen_store.mark_seen(job.dedup_key)
        records.append(record)

        if auto_ok:
            time.sleep(cooldown)

    seen_store.save()
    return records
