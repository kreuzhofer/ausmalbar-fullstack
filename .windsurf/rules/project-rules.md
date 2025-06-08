---
trigger: always_on
---

# Project Guidelines

This document contains project-specific guidelines to follow when generating or refactoring code. These guidelines supplement the standard coding standards defined in `CODING_STANDARDS.md`.

## General Guidelines

1. **Project Context**: This is a Django-based web application with Docker for containerization.
2. **Code Style**: Follow the existing code style and patterns already present in the codebase.
3. **Documentation**: Always add or update relevant docstrings and comments when modifying code.
4. **Code Generation**: Do not change code that is not directly related to the task at hand.

## Code Generation

### Django Models
- Use explicit `on_delete` parameters for all `ForeignKey` and `OneToOneField` fields
- Add `help_text` for fields where the purpose isn't immediately obvious
- Use `verbose_name` and `verbose_name_plural` for all models
- Add appropriate `related_name` for related fields to avoid reverse relation name conflicts
- Use `class Meta` for model metadata (ordering, indexes, permissions, etc.)

### Views
- Prefer class-based views over function-based views
- Use Django's built-in generic views when possible
- Keep view logic minimal, move business logic to services or model methods
- Use Django's `LoginRequiredMixin` for views that require authentication
- Use `UserPassesTestMixin` for permission checks

### Templates
- Use Django template language (DTL) for server-rendered templates
- Keep template logic to a minimum
- Use template inheritance with `{% extends %}` and `{% block %}`
- Use `{% include %}` for reusable components
- Use the `{% static %}` tag for static files
- Use the `{% url %}` tag for URL resolution

### Forms
- Use Django's ModelForm when working with models
- Add custom validation in forms when needed
- Use `clean_<fieldname>` for field-specific validation
- Use `clean()` for cross-field validation

## Internationalization
- always use prefixed translation identifiers based on the current file and context like imprint_ or home_.
- Never use the original text as language identifier. If you encounter such mistakes, offer to fix those issues in a refactoring step.
- Always create entries in the translation files for all languages (currently de/en) when introducing new translation ids. Don't introduce new languages besides those into the system unless explicitely asked to do so.

## Refactoring Guidelines

1. **Backward Compatibility**: Ensure changes don't break existing functionality
2. **Testing**: Update or add tests when refactoring
3. **Migrations**: Be cautious with model changes that require migrations
4. **Deprecation**: When changing public APIs, use deprecation warnings and maintain backward compatibility when possible

## Docker & Development Environment

1. **Container Usage**: Always use Docker for development and testing
2. **Docker Compose**: Use the defined services in `docker-compose.yml`
3. **Environment Variables**: Use environment variables for configuration, never hardcode sensitive information
4. **Dependencies**: Add new Python dependencies to `requirements.txt` or `requirements-dev.txt`
5. This project is using ONLY PostgreSQL. DO NOT TRY to connect to a SQLite database for any reason.
6. Every time you make a change that requires a rebuild or restart of the docker container, check if the db and web server are actually starting and if not, check the log files for reasons why.

## Security Guidelines

1. **Input Validation**: Always validate and sanitize user input
2. **Authentication**: Use Django's built-in authentication system
3. **Authorization**: Use Django's permission system for access control
4. **Secrets**: Never commit secrets or sensitive information to version control

## Performance

1. **Database Queries**: Use `select_related()` and `prefetch_related()` to optimize database queries
2. **Caching**: Use Django's cache framework for expensive operations
3. **Pagination**: Implement pagination for large result sets

## Testing

1. **Test Coverage**: Aim for high test coverage, especially for critical paths
2. **Test Types**: Write unit tests, integration tests, and end-to-end tests as appropriate
3. **Fixtures**: Use fixtures or factories for test data
4. **Mocks**: Use mocks for external services

## Documentation

1. **Docstrings**: Follow the Google Python Style Guide for docstrings
2. **Type Hints**: Use Python type hints for better code clarity and IDE support
3. **README**: Keep the project README up to date with setup and usage instructions

## Commit Messages

1. Follow the Conventional Commits specification
2. Reference relevant issues or tickets
3. Keep the summary line under 50 characters
4. Add a blank line between the summary and the body
5. Use the body to explain what and why, not how

## Code Review

1. **Self-Review**: Review your own code before submitting for review
2. **Small PRs**: Keep pull requests small and focused
3. **Descriptive Titles**: Use clear and descriptive PR titles
4. **Description**: Include a detailed description of changes and testing performed

## When in Doubt

When unsure about any of these guidelines:
1. Look at existing code for patterns
2. Ask the team for clarification
3. Document the decision for future reference