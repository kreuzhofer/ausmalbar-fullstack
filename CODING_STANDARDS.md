# Coding Standards

This document outlines the coding standards and development practices for the Ausmalbar Fullstack project.

## Python

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with a line length of 88 characters
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use [mypy](https://mypy.readthedocs.io/) for static type checking

### Pre-commit Hooks
We use pre-commit hooks to enforce code quality. To set up:

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the git hook scripts:
   ```bash
   pre-commit install
   ```

The following hooks are configured:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Static type checking
- **markdownlint**: Markdown file formatting
- **Trailing whitespace**: Removes trailing whitespace
- **End of file fixer**: Ensures files end with a newline

## JavaScript/TypeScript

### Code Style
- Use 2 spaces for indentation
- Use single quotes for strings
- Use semicolons at the end of statements
- Use ES6+ features when possible

## Git Workflow

### Branch Naming
- `feature/`: New features or enhancements
- `bugfix/`: Bug fixes
- `hotfix/`: Critical production fixes
- `chore/`: Maintenance tasks
- `docs/`: Documentation updates

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

## Code Review

- All changes must be submitted via pull requests
- At least one approval is required before merging
- All CI checks must pass before merging
- Keep pull requests focused and small when possible
- Include relevant tests with new features and bug fixes

## Documentation

- Keep documentation up-to-date with code changes
- Use docstrings for all public modules, classes, and functions
- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for docstrings

## Environment

- Use Python 3.8+ for development
- Use `pyproject.toml` for project configuration
- Use `requirements.txt` for production dependencies
- Use `requirements-dev.txt` for development dependencies

## VS Code Settings

Recommended settings for VS Code users (`.vscode/settings.json`):

```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.trimFinalNewlines": true
}
```
