"""
Enable pgvector extension and add embedding field to ColoringPage.
On PostgreSQL: creates a vector(3072) column.
On SQLite (tests): creates a nullable text column as placeholder.
"""
from django.db import connection, migrations, models


def enable_pgvector(apps, schema_editor):
    """Only run CREATE EXTENSION on PostgreSQL."""
    if connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def disable_pgvector(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute("DROP EXTENSION IF EXISTS vector;")


def add_vector_column(apps, schema_editor):
    """
    After Django adds the BinaryField column, alter it to vector type on PostgreSQL.
    On SQLite this is a no-op (the BinaryField column already exists).
    """
    if connection.vendor == "postgresql":
        schema_editor.execute(
            "ALTER TABLE coloring_pages_coloringpage "
            "ALTER COLUMN embedding TYPE vector(3072) USING embedding::vector(3072);"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('coloring_pages', '0019_add_trend_query'),
    ]

    operations = [
        migrations.RunPython(enable_pgvector, disable_pgvector),
        # Add a standard nullable column first (works on all backends)
        migrations.AddField(
            model_name='coloringpage',
            name='embedding',
            field=models.BinaryField(null=True, blank=True),
        ),
        # On PostgreSQL, convert it to a proper vector column
        migrations.RunPython(add_vector_column, migrations.RunPython.noop),
    ]
