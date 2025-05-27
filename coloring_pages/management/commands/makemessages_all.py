from django.core.management.base import BaseCommand
from django.core.management.commands import makemessages

class Command(BaseCommand):
    help = 'Create/update message files for all languages'

    def handle(self, *args, **options):
        # Create/update .po files for all languages
        self.stdout.write('Creating/updating message files...')
        makemessages.Command().execute(
            locale=['en', 'de'],
            ignore_patterns=['venv/*', 'node_modules/*'],
            no_obsolete=True,
            keep_pot=True,
            no_wrap=True,
            no_location=True,
            no_default_ignore=True,
            extensions=['py', 'html'],
            symlinks=False,
            use_default_ignore_patterns=True,
            verbosity=1,
        )
