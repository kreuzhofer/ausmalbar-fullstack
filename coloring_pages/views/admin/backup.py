import json
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
from django.views.decorators.http import require_POST

# In-memory store for restore tasks (single-server, single-process is fine here)
_restore_tasks = {}
_upload_sessions = {}


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
        return JsonResponse({"error": "No chunk data"}, status=400)

    # Create or retrieve upload session
    if upload_id not in _upload_sessions:
        tmpdir = tempfile.mkdtemp()
        _upload_sessions[upload_id] = {
            "tmpdir": tmpdir,
            "filepath": os.path.join(tmpdir, filename),
            "received": set(),
            "total_chunks": total_chunks,
        }

    session = _upload_sessions[upload_id]

    # Write chunk at correct offset
    with open(session["filepath"], "ab" if chunk_index > 0 else "wb") as f:
        # Seek to correct position for out-of-order chunks
        chunk_size = int(request.POST.get("chunk_size", chunk.size))
        f.seek(chunk_index * chunk_size)
        for part in chunk.chunks():
            f.write(part)

    session["received"].add(chunk_index)
    complete = len(session["received"]) >= session["total_chunks"]

    return JsonResponse({
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "received": len(session["received"]),
        "total_chunks": session["total_chunks"],
        "complete": complete,
    })


def _run_restore(task_id, archive_path, tmpdir):
    """Run the restore process in a background thread, updating progress."""
    task = _restore_tasks[task_id]
    try:
        task["status"] = "validating"
        task["message"] = "Validating backup archive..."

        if not zipfile.is_zipfile(archive_path):
            task["status"] = "error"
            task["message"] = "Not a valid ZIP file."
            return

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if "db.sql" not in names:
                task["status"] = "error"
                task["message"] = "Invalid backup: missing db.sql in archive."
                return
            media_count = sum(1 for n in names if n.startswith("media/"))

        db_settings = settings.DATABASES["default"]
        engine = db_settings["ENGINE"]
        if "postgresql" not in engine:
            task["status"] = "error"
            task["message"] = f"Restore only supports PostgreSQL. Current engine: {engine}"
            return

        # Extract archive
        task["status"] = "extracting"
        task["message"] = "Extracting backup archive..."
        extract_dir = os.path.join(tmpdir, "extracted")
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)

        # Restore database
        task["status"] = "restoring_db"
        task["message"] = "Restoring database..."
        dump_path = os.path.join(extract_dir, "db.sql")
        env = os.environ.copy()
        env["PGPASSWORD"] = db_settings.get("PASSWORD", "")

        db_name = db_settings.get("NAME", "ausmalbar")
        host = db_settings.get("HOST", "localhost")
        port = str(db_settings.get("PORT", "5432"))
        user = db_settings.get("USER", "postgres")

        psql_base = ["psql", "--host", host, "--port", port, "--username", user]

        # Terminate connections
        subprocess.run(
            psql_base + [
                "--dbname", "postgres", "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid();",
            ],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )

        # Drop and recreate
        subprocess.run(
            psql_base + ["--dbname", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name};"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )
        subprocess.run(
            psql_base + ["--dbname", "postgres", "-c", f"CREATE DATABASE {db_name};"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )

        # pg_restore
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
            task["status"] = "error"
            task["message"] = f"Database restore failed: {result.stderr.decode()}"
            return
        if result.returncode == 1:
            warnings = result.stderr.decode()

        task["message"] = "Database restored."

        # Restore media files
        task["status"] = "restoring_media"
        extracted_media = os.path.join(extract_dir, "media")
        if os.path.isdir(extracted_media):
            task["message"] = f"Restoring {media_count} media files..."
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
        else:
            media_count = 0

        # Done
        task["status"] = "complete"
        task["message"] = "Restore completed successfully."
        task["result"] = {
            "media_files": media_count,
            "warnings": warnings,
        }

    except Exception as e:
        task["status"] = "error"
        task["message"] = str(e)
    finally:
        # Clean up upload session and temp files
        shutil.rmtree(tmpdir, ignore_errors=True)


@require_POST
def restore_run(request):
    """Start the restore process from an uploaded file."""
    data = json.loads(request.body)
    upload_id = data.get("upload_id")

    if upload_id not in _upload_sessions:
        return JsonResponse({"error": "Upload session not found"}, status=404)

    session = _upload_sessions.pop(upload_id)
    archive_path = session["filepath"]
    tmpdir = session["tmpdir"]

    if not os.path.isfile(archive_path):
        return JsonResponse({"error": "Uploaded file not found"}, status=404)

    task_id = str(uuid.uuid4())
    _restore_tasks[task_id] = {
        "status": "starting",
        "message": "Starting restore...",
        "result": None,
    }

    thread = threading.Thread(
        target=_run_restore, args=(task_id, archive_path, tmpdir), daemon=True
    )
    thread.start()

    return JsonResponse({"task_id": task_id})


def restore_status(request, task_id):
    """Poll for restore progress."""
    task = _restore_tasks.get(task_id)
    if not task:
        return JsonResponse({"error": "Task not found"}, status=404)

    response = {
        "status": task["status"],
        "message": task["message"],
    }
    if task["result"]:
        response["result"] = task["result"]

    # Clean up completed/failed tasks after client reads them
    if task["status"] in ("complete", "error"):
        _restore_tasks.pop(task_id, None)

    return response


def restore_status_view(request, task_id):
    """Wrap restore_status to return JsonResponse."""
    result = restore_status(request, task_id)
    if isinstance(result, JsonResponse):
        return result
    return JsonResponse(result)


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
        path(
            "restore/status/<str:task_id>/",
            admin.site.admin_view(restore_status_view),
            name="restore_status",
        ),
    ]
