import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import uuid
import zipfile

from django.conf import settings
from django.contrib import admin, messages
from django.core.management import call_command
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# Base directory for all restore operations (shared across workers)
RESTORE_DIR = os.path.join(tempfile.gettempdir(), "ausmalbar_restore")


def _ensure_restore_dir():
    os.makedirs(RESTORE_DIR, exist_ok=True)


def _upload_dir(upload_id):
    return os.path.join(RESTORE_DIR, "uploads", upload_id)


def _task_file(task_id):
    return os.path.join(RESTORE_DIR, "tasks", f"{task_id}.json")


def _read_task(task_id):
    path = _task_file(task_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def _write_task(task_id, data):
    os.makedirs(os.path.dirname(_task_file(task_id)), exist_ok=True)
    # Write atomically to avoid partial reads
    tmp = _task_file(task_id) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, _task_file(task_id))


def backup_view(request):
    """Trigger a backup and stream the ZIP as a download."""
    if request.method != "POST":
        context = {
            **admin.site.each_context(request),
            "title": _("Backup"),
        }
        return TemplateResponse(
            request,
            "admin/coloring_pages/backup/backup.html",
            context,
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "ausmalbar_backup.zip")
            call_command("backup", output=output_path, stdout=open(os.devnull, "w"))
            response = FileResponse(
                open(output_path, "rb"),
                content_type="application/zip",
            )
            response["Content-Disposition"] = 'attachment; filename="ausmalbar_backup.zip"'
            return response
    except Exception as e:
        logger.exception("Backup failed")
        messages.error(request, _("Backup failed: %s") % str(e))
        return HttpResponseRedirect(reverse("admin:backup"))


def restore_view(request):
    """Render the restore page."""
    context = {
        **admin.site.each_context(request),
        "title": _("Restore"),
    }
    return TemplateResponse(
        request,
        "admin/coloring_pages/backup/restore.html",
        context,
    )


@require_POST
def restore_upload_chunk(request):
    """Receive a single chunk of the backup file."""
    upload_id = request.POST.get("upload_id")
    chunk_index = int(request.POST.get("chunk_index", 0))
    total_chunks = int(request.POST.get("total_chunks", 1))
    filename = request.POST.get("filename", "backup.zip")
    chunk = request.FILES.get("chunk")

    if not chunk:
        logger.warning("Upload chunk request with no chunk data, upload_id=%s", upload_id)
        return JsonResponse({"error": "No chunk data"}, status=400)

    # Create upload directory on disk (shared across workers)
    udir = _upload_dir(upload_id)
    os.makedirs(udir, exist_ok=True)

    # Write this chunk to its own file
    chunk_path = os.path.join(udir, f"chunk_{chunk_index:06d}")
    with open(chunk_path, "wb") as f:
        for part in chunk.chunks():
            f.write(part)

    # Write metadata
    meta_path = os.path.join(udir, "meta.json")
    meta = {"filename": filename, "total_chunks": total_chunks}
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    # Count received chunks
    received = len([n for n in os.listdir(udir) if n.startswith("chunk_")])
    complete = received >= total_chunks

    logger.info(
        "Chunk received: upload_id=%s, chunk=%d/%d, complete=%s",
        upload_id, chunk_index + 1, total_chunks, complete,
    )

    if complete:
        # Assemble chunks into final file
        filepath = os.path.join(udir, filename)
        with open(filepath, "wb") as out:
            for i in range(total_chunks):
                cp = os.path.join(udir, f"chunk_{i:06d}")
                with open(cp, "rb") as inp:
                    shutil.copyfileobj(inp, out)
        file_size = os.path.getsize(filepath)
        logger.info(
            "Upload complete: upload_id=%s, file_size=%.1f MB, path=%s",
            upload_id, file_size / (1024 * 1024), filepath,
        )

    return JsonResponse({
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "received": received,
        "total_chunks": total_chunks,
        "complete": complete,
    })


def _run_restore(task_id, archive_path, cleanup_dir):
    """Run the restore process in a background thread, updating progress on disk."""

    def update(status, message, result=None):
        _write_task(task_id, {
            "status": status,
            "message": message,
            "result": result,
        })

    try:
        # Validate
        update("validating", "Validating backup archive...")
        logger.info("[restore:%s] Validating archive: %s", task_id[:8], archive_path)

        if not zipfile.is_zipfile(archive_path):
            update("error", "Not a valid ZIP file.")
            logger.error("[restore:%s] Not a valid ZIP file", task_id[:8])
            return

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if "db.sql" not in names:
                update("error", "Invalid backup: missing db.sql in archive.")
                logger.error("[restore:%s] Missing db.sql in archive", task_id[:8])
                return
            media_count = sum(1 for n in names if n.startswith("media/"))

        logger.info(
            "[restore:%s] Archive valid: %d files, %d media files",
            task_id[:8], len(names), media_count,
        )

        # Extract
        update("extracting", "Extracting backup archive...")
        logger.info("[restore:%s] Extracting archive...", task_id[:8])
        extract_dir = os.path.join(cleanup_dir, "extracted")
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
        logger.info("[restore:%s] Extraction complete", task_id[:8])

        # Restore database
        update("restoring_db", "Restoring database...")
        dump_path = os.path.join(extract_dir, "db.sql")
        env = os.environ.copy()

        db_settings = settings.DATABASES["default"]
        env["PGPASSWORD"] = db_settings.get("PASSWORD", "")
        db_name = db_settings.get("NAME", "ausmalbar")
        host = db_settings.get("HOST", "localhost")
        port = str(db_settings.get("PORT", "5432"))
        user = db_settings.get("USER", "postgres")

        psql_base = ["psql", "--host", host, "--port", port, "--username", user]

        # Terminate connections
        logger.info("[restore:%s] Terminating existing DB connections...", task_id[:8])
        subprocess.run(
            psql_base + [
                "--dbname", "postgres", "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();",
            ],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )

        # Drop and recreate
        logger.info("[restore:%s] Dropping and recreating database '%s'...", task_id[:8], db_name)
        subprocess.run(
            psql_base + ["--dbname", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name};"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )
        subprocess.run(
            psql_base + ["--dbname", "postgres", "-c", f"CREATE DATABASE {db_name};"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )

        # pg_restore
        logger.info("[restore:%s] Running pg_restore...", task_id[:8])
        result = subprocess.run(
            [
                "pg_restore", "--host", host, "--port", port,
                "--username", user, "--dbname", db_name,
                "--no-owner", "--no-acl", dump_path,
            ],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        warnings = ""
        if result.returncode > 1:
            stderr = result.stderr.decode()
            update("error", f"Database restore failed: {stderr}")
            logger.error("[restore:%s] pg_restore failed (code %d): %s", task_id[:8], result.returncode, stderr)
            return
        if result.returncode == 1:
            warnings = result.stderr.decode()
            logger.warning("[restore:%s] pg_restore warnings: %s", task_id[:8], warnings)

        logger.info("[restore:%s] Database restored successfully", task_id[:8])

        # Restore media files
        update("restoring_media", f"Restoring {media_count} media files...")
        extracted_media = os.path.join(extract_dir, "media")
        if os.path.isdir(extracted_media):
            logger.info("[restore:%s] Restoring %d media files...", task_id[:8], media_count)
            media_root = settings.MEDIA_ROOT
            # Clear contents (not the dir itself — it may be a Docker volume mount)
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
            logger.info("[restore:%s] Media files restored", task_id[:8])
        else:
            media_count = 0
            logger.info("[restore:%s] No media files in backup", task_id[:8])

        # Done
        update("complete", "Restore completed successfully.", {
            "media_files": media_count,
            "warnings": warnings,
        })
        logger.info("[restore:%s] Restore complete. Media files: %d", task_id[:8], media_count)

    except Exception as e:
        update("error", str(e))
        logger.exception("[restore:%s] Restore failed with exception", task_id[:8])
    finally:
        # Clean up extracted files but keep the task status file
        shutil.rmtree(cleanup_dir, ignore_errors=True)


@require_POST
def restore_run(request):
    """Start the restore process from an uploaded file."""
    data = json.loads(request.body)
    upload_id = data.get("upload_id")

    udir = _upload_dir(upload_id)
    meta_path = os.path.join(udir, "meta.json")
    if not os.path.exists(meta_path):
        logger.error("Restore run: upload session not found for upload_id=%s", upload_id)
        return JsonResponse({"error": "Upload session not found"}, status=404)

    with open(meta_path, "r") as f:
        meta = json.load(f)

    archive_path = os.path.join(udir, meta["filename"])
    if not os.path.isfile(archive_path):
        logger.error("Restore run: assembled file not found at %s", archive_path)
        return JsonResponse({"error": "Uploaded file not found"}, status=404)

    task_id = str(uuid.uuid4())
    _write_task(task_id, {
        "status": "starting",
        "message": "Starting restore...",
        "result": None,
    })

    logger.info(
        "Starting restore: task_id=%s, upload_id=%s, archive=%s (%.1f MB)",
        task_id[:8], upload_id, archive_path,
        os.path.getsize(archive_path) / (1024 * 1024),
    )

    thread = threading.Thread(
        target=_run_restore, args=(task_id, archive_path, udir), daemon=True
    )
    thread.start()

    return JsonResponse({"task_id": task_id})


def restore_status_view(request, task_id):
    """Poll for restore progress. No auth required — task_id acts as a token.
    State is read from disk so any worker process can serve this."""
    task = _read_task(task_id)
    if not task:
        logger.debug("Status poll for unknown task_id=%s", task_id[:8] if task_id else "none")
        return JsonResponse({"error": "Task not found"}, status=404)

    response = {
        "status": task["status"],
        "message": task["message"],
    }
    if task.get("result"):
        response["result"] = task["result"]

    # Clean up completed/failed task files after client reads them
    if task["status"] in ("complete", "error"):
        logger.info(
            "Task %s finished with status=%s, cleaning up task file",
            task_id[:8], task["status"],
        )
        try:
            os.remove(_task_file(task_id))
        except OSError:
            pass

    return JsonResponse(response)


def get_backup_urls():
    """Return URL patterns for backup/restore, wrapped with admin permission checks."""
    return [
        path(
            "backup/",
            admin.site.admin_view(backup_view),
            name="backup",
        ),
        path(
            "restore/",
            admin.site.admin_view(restore_view),
            name="restore",
        ),
        path(
            "restore/upload-chunk/",
            admin.site.admin_view(restore_upload_chunk),
            name="restore_upload_chunk",
        ),
        path(
            "restore/run/",
            admin.site.admin_view(restore_run),
            name="restore_run",
        ),
        # Status endpoint is NOT wrapped with admin_view — the DB is gone
        # during restore so session auth would fail. The UUID task_id serves
        # as an unguessable token. State is on disk, readable by any worker.
        path(
            "restore/status/<str:task_id>/",
            csrf_exempt(restore_status_view),
            name="restore_status",
        ),
    ]
