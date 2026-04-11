"""
Enable pgvector extension and add embedding field to ColoringPage.
On PostgreSQL: creates a proper vector(3072) column.
On SQLite (tests): standard AddField creates a compatible column.
"""
from django.db import connection, migrations

from pgvector.django import VectorField


def enable_pgvector_extension(apps, schema_editor):
    """Enable the vector extension on PostgreSQL only."""
    if connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def disable_pgvector_extension(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute("DROP EXTENSION IF EXISTS vector;")


class Migration(migrations.Migration):

    dependencies = [
        ('coloring_pages', '0019_add_trend_query'),
    ]

    operations = [
        # Step 1: Enable pgvector extension (no-op on SQLite)
        migrations.RunPython(enable_pgvector_extension, disable_pgvector_extension),
        # Step 2: Add the field. VectorField maps to vector(3072) on PostgreSQL
        # and falls back gracefully on SQLite.
        migrations.AddField(
            model_name='coloringpage',
            name='embedding',
            field=VectorField(dimensions=3072, null=True, blank=True),
        ),
    ]
