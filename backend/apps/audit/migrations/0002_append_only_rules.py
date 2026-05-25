"""
Custom migration to add PostgreSQL rules that prevent UPDATE and DELETE
on the audit_auditevent table, enforcing append-only behaviour at the
database level.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Block UPDATE on audit events
                """
                CREATE OR REPLACE RULE audit_event_no_update AS
                    ON UPDATE TO audit_auditevent
                    DO INSTEAD NOTHING;
                """,
                # Block DELETE on audit events
                """
                CREATE OR REPLACE RULE audit_event_no_delete AS
                    ON DELETE TO audit_auditevent
                    DO INSTEAD NOTHING;
                """,
            ],
            reverse_sql=[
                "DROP RULE IF EXISTS audit_event_no_update ON audit_auditevent;",
                "DROP RULE IF EXISTS audit_event_no_delete ON audit_auditevent;",
            ],
        ),
    ]
