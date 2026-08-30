# Job Agent

Searches job postings, generates a resume and cover letter tailored to each
one, and (for a deliberately limited set of sources) auto-submits the
application through a real browser. Built for one candidate profile
(`profile/profile.json`), targeting AI/GenAI Product Owner, Head of AI, and
Director of AI Engineering roles in India.

## Why it's built this way

Maximizing interview callbacks means two things working together:
1. **Every application should be genuinely tailored** — matching the JD's
   language (for ATS keyword matching) and leading with the most relevant
   parts of the real work history, without ever fabricating anything.
2. **Auto-apply has to respect where automation is actually safe.** Job
   boards are not uniform:
   - **Greenhouse / Lever** postings use simple, standardized forms and the
     company (not the board) owns the ToS — applicant-side automation here
     is low risk. This tool *can* auto-submit to these.
   - **LinkedIn** aggressively detects and bans automated Easy Apply /
     scraping. This tool **never** auto-submits to LinkedIn, no matter what
     `config.yaml` says — it's a hard-coded guard in
     `src/job_agent/apply/safety.py`, not just a config default.
   - **Indeed** has no public search/apply API for this use case. Jobs come
     in via a JSON file you export (see below), and are always staged for
     manual submission, never auto-submitted.

So in practice: Greenhouse/Lever get full search → tailor → auto-apply.
Indeed and LinkedIn get search → tailor → **staged in `outbox/`** for you to
submit by hand in a couple of clicks.

## Setup

```bash
cd job_agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Only if you want real browser auto-apply (Greenhouse/Lever):
pip install playwright && playwright install chromium

# Only if you want LLM-polished resume/cover-letter phrasing:
pip install anthropic
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Configure

Edit `config/config.yaml`:
- `sources.greenhouse.boards` / `sources.lever.boards` — add the company
  board tokens/slugs you want to track (found in that company's careers
  page URL, e.g. `boards.greenhouse.io/<token>` or `jobs.lever.co/<slug>`).
- `apply.dry_run` — **leave this `true`** until you've reviewed dry-run
  output (`data/applications_log.csv`) and trust the pipeline. Dry run
  fills out the real form and stops one click before submit.
- `apply.max_applications_per_day` / `cooldown_seconds_between_applications`
  — rate limits so this doesn't look like a bot to the sites it touches.

Your profile lives in `profile/profile.json`. Update it directly if your
resume changes — every generated document is built from this file only.

## Pulling in Indeed / LinkedIn postings

Neither site offers a scrape/auto-apply-friendly API. Instead:

- **Indeed**: if you're running this from an interactive Claude Code
  session with the Indeed MCP connector attached, ask it to search jobs
  and save the results to `data/indeed_jobs.json` in the schema documented
  at the top of `src/job_agent/sources/indeed_import.py`.
- **LinkedIn**: manually copy postings you find into
  `data/linkedin_jobs.json`, schema documented in
  `src/job_agent/sources/linkedin_import.py`.

Both files are optional — leave them absent/empty and those sources are
simply skipped.

## Run

```bash
python -m job_agent.cli run --config config/config.yaml
```

Each run:
1. Searches all enabled sources.
2. Skips postings already processed in a previous run (`data/jobs_seen.json`).
3. Scores remaining postings against your profile (`src/job_agent/matching.py`)
   and drops anything below `search.min_match_score`.
4. For each match: builds a tailored resume + cover letter, renders them to
   PDF, and either auto-applies (Greenhouse/Lever, subject to the guard) or
   stages them in `outbox/<company>__<title>__<id>/` with a `note.txt`
   explaining the match and the apply URL.
5. Logs every outcome to `data/applications_log.csv` — use this to track
   your funnel (applied → response → interview) over time.

## Tests

```bash
pip install pytest
pytest tests/
```

Tests cover matching/scoring, keyword extraction, resume/cover-letter
generation (including that no facts are ever fabricated), PDF rendering,
and the apply-safety guard (in particular, that LinkedIn can never be
auto-submitted even if misconfigured).

## Known limitations

- Greenhouse/Lever form-filling uses common field selectors; a company that
  heavily customizes their form with required custom questions this tool
  can't answer will fall back to staging rather than submitting a broken
  application — check `outbox/` for those.
- This is not a guarantee against a job board's bot detection. Keep
  `max_applications_per_day` conservative and don't run this so frequently
  that it looks automated, because — for the sources it does touch — it is.
