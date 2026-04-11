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
```

After any rebuild/restart, verify both db and web containers are running and check logs for errors.

## Testing

Tests use in-memory SQLite. Always run tests after rebuilding containers.

```bash
# Run all tests
docker-compose exec web python -m pytest coloring_pages/tests/

# Run a single test file
docker-compose exec web python -m pytest coloring_pages/tests/frontend/test_frontend_urls.py

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

### Key Models

- **ColoringPage** — Bilingual title/description/SEO-URL fields (`_en`/`_de` suffixes), image + auto-generated WebP thumbnail, prompt, JSON metadata
- **SystemPrompt** — Stores AI prompt templates with model provider/name and quality settings
- **SearchQuery** — Tracks user searches with 5-minute deduplication window, captures session/IP/language/referrer

### Views Organization

Views are split into modules under `coloring_pages/views/`:
- `home.py`, `search.py`, `detail.py` — Public pages
- `admin/` — Custom generation UI (generate form → confirmation/preview)
- `views_legal.py` — Imprint, privacy, ToS (class-based)

### URL Pattern

SEO URLs serve both languages: `/coloring-page/<slug>/` (EN) and `/ausmalbild/<slug>/` (DE). Django's `i18n_patterns` handles locale prefixing with domain-based language routing via middleware.

### Management Commands

- `wait_for_db` — Blocks until PostgreSQL is ready (used in container startup)
- `makemessages_all` — Extract translation strings for all languages
- `generate_sitemap`, `load_sample_data`, `check_health`, `initdb`

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
