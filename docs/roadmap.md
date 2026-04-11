# Ausmalbar Roadmap

Project started: May 2025

---

## Done

### Core Application

- [x] Django project setup with Docker and PostgreSQL
- [x] Coloring page generation via OpenAI DALL-E
- [x] Custom admin interface for image generation workflow
- [x] Image regeneration with editable prompts
- [x] Auto-translation of titles and descriptions (DE/EN)
- [x] Bilingual content with domain-based language routing
- [x] SEO-optimized URLs (`/coloring-page/<slug>/`, `/ausmalbild/<slug>/`)
- [x] Django i18n with prefixed translation identifiers
- [x] Search functionality with query tracking
- [x] Popular searches display
- [x] Detail page with descriptions
- [x] Clickable image previews
- [x] Social share buttons
- [x] Download button for coloring pages
- [x] WebP thumbnail auto-generation
- [x] Favicons

### Admin & Content Management

- [x] SystemPrompt model for managing AI prompt templates
- [x] SystemPrompt duplication feature
- [x] Multiline prompt field in admin
- [x] Generate form with confirmation/preview workflow
- [x] Progress indicator for image generation and regeneration
- [x] SearchQuery tracking in admin (session, IP, language, referrer)
- [x] 5-minute search deduplication window

### Infrastructure & DevOps

- [x] Docker Compose setup (dev with runserver, prod with gunicorn)
- [x] GitHub Actions CI for Docker image builds
- [x] Production Dockerfile optimization
- [x] Container health check command
- [x] `wait_for_db` startup command
- [x] `initdb` management command
- [x] Environment-based configuration via `.env`

### SEO & Analytics

- [x] Dynamic sitemap generation (multi-language)
- [x] robots.txt
- [x] ads.txt for Google AdSense
- [x] Google AdSense integration
- [x] Mixpanel server-side tracking
- [x] Domain-based language detection middleware

### Legal & Compliance

- [x] Imprint / Impressum page
- [x] Privacy policy
- [x] Terms of service

### Code Quality & Testing

- [x] pytest test suite with SQLite for tests
- [x] Coverage reporting
- [x] Frontend URL tests
- [x] Pre-commit hooks (Black, isort, Flake8, mypy)
- [x] Conventional Commits with commitizen
- [x] Views refactored into modular structure
- [x] Admin views refactored into modules
- [x] OpenAI usage centralized into single function
- [x] CLAUDE.md project guidelines

---

## Planned

### Backup & Restore

Full backup and restore functionality accessible from the admin interface.

- [x] Management command to export full database dump (PostgreSQL)
- [x] Management command to bundle all generated images and media files
- [x] Create downloadable ZIP archive containing DB dump + media
- [x] Admin UI page to trigger backup and download the ZIP
- [x] Admin UI page to upload a backup ZIP and restore (overwrite DB + media)
- [x] Restore confirmation step with warnings about data overwrite
- [ ] Documentation for manual server migration using backup files

### AI-Assisted Daily Image Generation

Automatically generate new coloring pages based on user demand signals.

- [ ] Analyse SearchQuery entries that returned few or no results
- [ ] Cluster and rank unmet search terms by frequency
- [ ] Daily scheduled task to pick top unmet query and generate a coloring page
- [ ] Admin dashboard showing unmet demand queue and generation history
- [ ] Option to approve/reject AI-suggested images before publishing

### Google Trends Integration

Leverage trending search data to proactively create popular coloring pages.

- [ ] Integrate Google Trends API (pytrends) for Germany-specific trends
- [ ] Integrate worldwide trending searches related to coloring pages
- [ ] Filter and rank trends relevant to children's coloring content
- [ ] Admin dashboard showing current trends and suggested topics
- [ ] Semi-automated generation pipeline: trend detected, prompt suggested, admin approves

### Content & Discovery Improvements

- [ ] Category/tag system for coloring pages (animals, vehicles, seasons, etc.)
- [ ] Browse-by-category pages with SEO-friendly URLs
- [ ] "Related coloring pages" suggestions on detail pages
- [ ] Seasonal and holiday-themed collections (Christmas, Easter, Halloween)
- [ ] Pagination or infinite scroll for large result sets

### User Engagement

- [ ] "Most popular" / "Trending" section on homepage
- [ ] Recently added coloring pages feed
- [ ] Email newsletter signup for new coloring pages
- [ ] User ratings or favorites (anonymous, cookie-based)
- [ ] Print-optimized CSS for direct browser printing

### Performance & Scalability

- [ ] CDN integration for static and media files
- [ ] Redis caching for frequently accessed pages
- [ ] Image lazy loading on listing pages
- [ ] Database query optimization audit
- [ ] Load testing and performance benchmarks

### Monitoring & Analytics

- [ ] Admin analytics dashboard (searches, downloads, page views)
- [ ] Alerting for failed image generations
- [ ] Search conversion tracking (search to download funnel)
- [ ] A/B testing framework for prompts and layouts
