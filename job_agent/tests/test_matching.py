from job_agent.matching import MatchConfig, rank_jobs, score_job
from job_agent.models import JobPosting

CFG = MatchConfig(
    target_titles=["Head of AI", "AI Product Owner"],
    keywords_any=["Generative AI", "Agentic AI", "MLOps"],
    min_years_experience=8,
    min_match_score=0.1,
    country="India",
)


def make_job(**overrides):
    defaults = dict(
        source="greenhouse",
        external_id="1",
        title="Head of AI",
        company="Acme",
        location="Bengaluru, India",
        description="Lead our Generative AI and Agentic AI strategy using MLOps and Azure OpenAI.",
        apply_url="https://example.com/apply",
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_relevant_senior_role_scores_high(profile):
    job = make_job()
    result = score_job(job, profile, CFG)
    assert result.score > 0.5
    assert "Generative AI" in result.matched_keywords or "generative ai" in [k.lower() for k in result.matched_keywords]


def test_irrelevant_role_scores_low(profile):
    job = make_job(title="Warehouse Associate", description="Lift boxes and operate a forklift.")
    result = score_job(job, profile, CFG)
    assert result.score < 0.2


def test_rank_jobs_filters_below_threshold(profile):
    cfg = MatchConfig(**{**CFG.__dict__, "min_match_score": 0.9})
    jobs = [make_job(), make_job(external_id="2", title="Warehouse Associate", description="forklift")]
    ranked = rank_jobs(jobs, profile, cfg)
    assert ranked == []
