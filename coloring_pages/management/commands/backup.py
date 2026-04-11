import os
import subprocess
import tempfile
import zipfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Create a backup ZIP containing a PostgreSQL dump and all media files."""

    help = "Export database and media files into a single ZIP archive."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=None,
            help="Output path for the backup ZIP. Defaults to /tmp/ausmalbar_backup_<timestamp>.zip",
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = options["output"] or os.path.join(
            tempfile.gettempdir(), f"ausmalbar_backup_{timestamp}.zip"
        )

        db_settings = settings.DATABASES["default"]
        engine = db_settings["ENGINE"]
        if "postgresql" not in engine:
            raise CommandError(
                f"Backup only supports PostgreSQL. Current engine: {engine}"
            )

        self.stdout.write("Starting backup...")

        with tempfile.TemporaryDirectory() as tmpdir:
            # --- Database dump ---
            dump_path = os.path.join(tmpdir, "db.sql")
            self.stdout.write("  Dumping database...")
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.get("PASSWORD", "")
            cmd = [
                "pg_dump",
                "--host",
                db_settings.get("HOST", "localhost"),
                "--port",
                str(db_settings.get("PORT", "5432")),
                "--username",
                db_settings.get("USER", "postgres"),
                "--format",
                "custom",
                "--no-owner",
                "--no-acl",
                db_settings.get("NAME", "ausmalbar"),
            ]
            try:
                with open(dump_path, "wb") as f:
                    subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE, check=True)
            except FileNotFoundError:
                raise CommandError(
                    "pg_dump not found. Ensure PostgreSQL client tools are installed."
                )
            except subprocess.CalledProcessError as e:
                raise CommandError(f"pg_dump failed: {e.stderr.decode()}")

            self.stdout.write(self.style.SUCCESS("  Database dump complete."))

            # --- Build ZIP ---
            self.stdout.write("  Creating ZIP archive...")
            media_root = settings.MEDIA_ROOT
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add database dump
                zf.write(dump_path, "db.sql")

                # Add media files
                if os.path.isdir(media_root):
                    for dirpath, _dirnames, filenames in os.walk(media_root):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            arcname = os.path.join(
                                "media",
                                os.path.relpath(filepath, media_root),
                            )
                            zf.write(filepath, arcname)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Backup complete: {output_path} ({size_mb:.1f} MB)"
                )
            )
        return output_path
