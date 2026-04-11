import os
import tempfile

from django.contrib import admin, messages
from django.core.management import call_command
from django.http import FileResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _


class BackupRestoreAdmin(admin.ModelAdmin):
    """Phantom ModelAdmin that provides backup/restore views without a real model."""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
    """Upload a backup ZIP and restore from it."""
    if request.method != "POST":
        context = {
            **admin.site.each_context(request),
            "title": _("Restore"),
        }
        return TemplateResponse(
            request,
            "admin/coloring_pages/backup/restore.html",
            context,
        )

    uploaded = request.FILES.get("backup_file")
    if not uploaded:
        messages.error(request, _("No file uploaded."))
        return HttpResponseRedirect(reverse("admin:restore"))

    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".zip", delete=False
        ) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        call_command("restore", tmp_path, no_confirm=True, stdout=open(os.devnull, "w"))
        messages.success(request, _("Restore completed successfully. The database and media files have been replaced."))
    except Exception as e:
        messages.error(request, _("Restore failed: %s") % str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return HttpResponseRedirect(reverse("admin:restore"))


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
    ]
