# Internationalization (i18n) Setup

This document outlines the internationalization setup for the Ausmalbar application.

## Supported Languages

- English (en) - Default
- German (de)

## Adding New Translations

1. **Mark strings for translation** in Python code:
   ```python
   from django.utils.translation import gettext_lazy as _
   
   message = _("This is a translatable string.")
   ```

2. **Mark strings in templates**:
   ```html
   {% load i18n %}
   {% trans "This is a translatable string" %}
   
   {% blocktrans %}This is a block of translatable text.{% endblocktrans %}
   ```

3. **Create or update translation files**:
   ```bash
   # Create or update .po files
   python manage.py makemessages -l de
   
   # Compile .po files to .mo
   python manage.py compilemessages
   ```

4. **Add translations** to the corresponding `.po` file in `locale/<lang>/LC_MESSAGES/django.po`

## Translation Files Structure

- `locale/` - Root directory for all translations
  - `en/` - English translations
    - `LC_MESSAGES/`
      - `django.po` - Translation file
      - `django.mo` - Compiled translation file (generated)
  - `de/` - German translations
    - `LC_MESSAGES/`
      - `django.po` - Translation file
      - `django.mo` - Compiled translation file (generated)

## Language Switcher

A language switcher is available in the top-right corner of the page. It shows the available languages and allows users to switch between them.

## Testing Translations

You can test the internationalization setup by visiting:
- `/test-i18n/` - A test page showing various translation examples

## Adding a New Language

1. Add the language to `LANGUAGES` in `settings.py`
2. Create a new directory for the language in `locale/`
3. Generate the translation file:
   ```bash
   python manage.py makemessages -l <language_code>
   ```
4. Add translations to the new `.po` file
5. Compile the translations:
   ```bash
   python manage.py compilemessages
   ```

## Best Practices

1. Always use the `_()` function for strings that need translation in Python code
2. Use `{% trans %}` or `{% blocktrans %}` tags in templates
3. Keep translations up to date when adding new features
4. Test the application in all supported languages
5. Consider right-to-left (RTL) languages if needed for future translations
