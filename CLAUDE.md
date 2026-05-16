# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ausmalbar is a Django web application that generates AI-powered coloring pages using OpenAI's DALL-E. It serves bilingual content (German/English) with domain-based language routing, SEO-optimized URLs, and a custom admin interface for image generation.

## Development Environment

The project runs entirely in Docker. PostgreSQL is the **only** database for dev and prod — never use SQLite except in test cases.

```bash
# Start development (uses docker-compose.override.yml → Django runserver with DEBUG=True)
docker-compose up -d

# Rebuild after dependency or Dockerfile changes
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Run Django management commands
docker-compose exec web python manage.py <command>

# Production (separate compose file)
docker-compose -f docker-compose.prod.yml up -d
```

After any rebuild/restart, verify both db and web containers are running and check logs for errors.

## Testing

Tests use in-memory SQLite. Always run tests after rebuilding containers.

```bash
# Run all tests
docker-compose exec web python -m pytest coloring_pages/tests/

# Run a single test file
docker-compose exec web python -m pytest coloring_pages/tests/frontend/test_frontend_urls.py

# Frontend URL accessibility tests use a dedicated settings module
docker-compose exec web python manage.py test \
  coloring_pages.tests.frontend.test_frontend_urls \
  --settings=coloring_pages.tests.frontend.test_settings

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

## Code Quality

Pre-commit hooks enforce formatting. Configuration is in `pyproject.toml`:

- **Black**: line length 88
- **isort**: black-compatible profile
- **Flake8**: max complexity 10, ignores E203/W503
- **mypy**: strict (disallow_untyped_defs)

## Architecture

### Django Apps

- **`ausmalbar/`** — Project settings, WSGI, middleware (MixpanelTracking, DomainLanguageRedirect), context processors
- **`coloring_pages/`** — Main app: models, views, templates, admin, management commands, tests

### Key Modules

Top-level helpers inside `coloring_pages/` worth knowing about:
- `embeddings.py` + `embed_pages` command — vector embeddings for coloring pages (similarity / related-page features)
- `suggestions.py` — AI-generated suggestion pipeline; suggestions are persisted via the `Suggestion` model for async review (see recent commits around demand/suggestions workflow)
- `demand.py` — demand-tracking / dashboard support (paired with `views/admin/demand.py`)
- `trends.py` — trend computation backing the `Trend` model
- `storage_backends.py` — S3 storage backend, activated when AWS env vars are set
- `sitemaps.py` + `generate_sitemap` command — sitemap generation
- `templatetags/` — custom template tags used in templates

### Models (`coloring_pages/models/` is a package)

- **`coloring_page.py` — ColoringPage** — Bilingual title/description/SEO-URL fields (`_en`/`_de` suffixes), image + auto-generated WebP thumbnail, prompt, JSON metadata
- **`system_prompt.py` — SystemPrompt** — Stores AI prompt templates with model provider/name and quality settings
- **`search.py` — SearchQuery** — Tracks user searches with 5-minute deduplication window, captures session/IP/language/referrer
- **`suggestion.py` — Suggestion** — Persisted AI suggestions awaiting review/publication (drives the demand dashboard)
- **`trend.py` — Trend** — Trend records derived from `trends.py`
- **`schedule.py` — Schedule** — Definitions consumed by the `run_scheduler` command for periodic jobs (e.g. `generate_daily`)
- **`base.py`** — Shared mixins / abstract base used by other models

### Views Organization

Views are split into modules under `coloring_pages/views/`:
- `home.py`, `search.py`, `detail.py` — Public pages
- `errors.py`, `robots.py`, `sitemap.py` — Error handlers, robots.txt, sitemap
- `views_class_based.py`, `views_legal.py` — Class-based public views including legal pages (imprint, privacy, ToS)
- `admin/` — Custom admin UI. Not just generation: contains `generate_coloring_page_view.py` + `confirm_coloring_page_view.py` (the generate → confirm/preview flow), plus full management views in `coloring_page.py`, `system_prompt.py`, `search.py`, `demand.py`, and `backup.py`

### URL Pattern

SEO URLs serve both languages: `/coloring-page/<slug>/` (EN) and `/ausmalbild/<slug>/` (DE). Django's `i18n_patterns` handles locale prefixing with domain-based language routing via middleware.

### Management Commands

- `wait_for_db` — Blocks until PostgreSQL is ready (used in container startup)
- `makemessages_all` — Extract translation strings for all languages
- `generate_sitemap`, `load_sample_data`, `check_health`, `initdb`
- `embed_pages` — Compute / refresh embeddings for existing coloring pages
- `generate_daily` — Daily AI generation job (intended to run via the scheduler)
- `run_scheduler` — Long-running scheduler that dispatches jobs defined by `Schedule` records
- `backup`, `restore` — Database/media backup and restore helpers

## Internationalization

- Use **prefixed translation identifiers** based on file/context (e.g., `home_title`, `imprint_heading`). Never use raw text as translation keys.
- Always create entries in **both** `locale/de/` and `locale/en/` when adding new translation IDs.
- Do not introduce new languages unless explicitly asked.

## Conventions

- Follow Conventional Commits for commit messages (enforced by commitizen)
- Prefer class-based views over function-based views
- Use `select_related()`/`prefetch_related()` for query optimization
- Use explicit `on_delete` for ForeignKey fields
- Add `verbose_name`/`verbose_name_plural` on models
- Dependencies go in `requirements.txt` (prod) or `requirements-dev.txt` (dev)

## Related Docs

- `CODING_STANDARDS.md` — Python/JS style, pre-commit hooks, git workflow
- `README_i18n.md` — Detailed translation workflow (`makemessages` / `compilemessages`, locale layout)
- `.windsurf/rules/project-rules.md` — Source-of-truth project guidelines (the conventions above mirror it)
- `README.md` — End-user setup, production deployment, backup/restore recipes
