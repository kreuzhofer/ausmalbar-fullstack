import os
import shutil
import subprocess
import tempfile
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Restore database and media files from a backup ZIP created by the backup command."""

    help = "Restore database and media from a backup ZIP archive."

    def add_arguments(self, parser):
        parser.add_argument("archive", type=str, help="Path to the backup ZIP file.")
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            default=False,
            help="Skip the confirmation prompt.",
        )

    def handle(self, *args, **options):
        archive_path = options["archive"]
        if not os.path.isfile(archive_path):
            raise CommandError(f"File not found: {archive_path}")

        if not zipfile.is_zipfile(archive_path):
            raise CommandError(f"Not a valid ZIP file: {archive_path}")

        # Validate archive contents
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if "db.sql" not in names:
                raise CommandError("Invalid backup: missing db.sql in archive.")
            media_count = sum(1 for n in names if n.startswith("media/"))

        db_settings = settings.DATABASES["default"]
        engine = db_settings["ENGINE"]
        if "postgresql" not in engine:
            raise CommandError(
                f"Restore only supports PostgreSQL. Current engine: {engine}"
            )

        if not options["no_confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\nThis will OVERWRITE the current database and {media_count} media files."
                )
            )
            self.stdout.write(
                self.style.WARNING("This action cannot be undone!\n")
            )
            confirm = input("Type 'yes' to continue: ")
            if confirm.strip().lower() != "yes":
                self.stdout.write("Restore cancelled.")
                return

        self.stdout.write("Starting restore...")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract archive
            self.stdout.write("  Extracting archive...")
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(tmpdir)

            # --- Restore database ---
            dump_path = os.path.join(tmpdir, "db.sql")
            self.stdout.write("  Restoring database...")
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.get("PASSWORD", "")

            db_name = db_settings.get("NAME", "ausmalbar")
            host = db_settings.get("HOST", "localhost")
            port = str(db_settings.get("PORT", "5432"))
            user = db_settings.get("USER", "postgres")

            # Drop and recreate the database
            psql_base = ["psql", "--host", host, "--port", port, "--username", user]
            try:
                # Terminate existing connections
                subprocess.run(
                    psql_base
                    + [
                        "--dbname",
                        "postgres",
                        "-c",
                        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();",
                    ],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=True,
                )

                # Drop and recreate
                subprocess.run(
                    psql_base + ["--dbname", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name};"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                subprocess.run(
                    psql_base + ["--dbname", "postgres", "-c", f"CREATE DATABASE {db_name};"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=True,
                )

                # Restore from dump (exit code 1 = warnings, only fail on >= 2)
                result = subprocess.run(
                    [
                        "pg_restore",
                        "--host",
                        host,
                        "--port",
                        port,
                        "--username",
                        user,
                        "--dbname",
                        db_name,
                        "--no-owner",
                        "--no-acl",
                        dump_path,
                    ],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                if result.returncode > 1:
                    raise subprocess.CalledProcessError(
                        result.returncode, "pg_restore", stderr=result.stderr
                    )
                if result.returncode == 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  pg_restore warnings: {result.stderr.decode()}"
                        )
                    )
            except FileNotFoundError:
                raise CommandError(
                    "psql/pg_restore not found. Ensure PostgreSQL client tools are installed."
                )
            except subprocess.CalledProcessError as e:
                raise CommandError(f"Database restore failed: {e.stderr.decode()}")

            self.stdout.write(self.style.SUCCESS("  Database restored."))

            # --- Restore media files ---
            extracted_media = os.path.join(tmpdir, "media")
            if os.path.isdir(extracted_media):
                media_root = settings.MEDIA_ROOT
                self.stdout.write(f"  Restoring {media_count} media files...")

                # Clear existing media contents (not the dir itself — it may be a mount)
                if os.path.isdir(media_root):
                    for entry in os.listdir(media_root):
                        entry_path = os.path.join(media_root, entry)
                        if os.path.isdir(entry_path):
                            shutil.rmtree(entry_path)
                        else:
                            os.remove(entry_path)
                else:
                    os.makedirs(media_root)
                # Copy restored media into the directory
                for entry in os.listdir(extracted_media):
                    src = os.path.join(extracted_media, entry)
                    dst = os.path.join(media_root, entry)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                self.stdout.write(self.style.SUCCESS("  Media files restored."))
            else:
                self.stdout.write("  No media files in backup.")

        self.stdout.write(self.style.SUCCESS("Restore complete."))
