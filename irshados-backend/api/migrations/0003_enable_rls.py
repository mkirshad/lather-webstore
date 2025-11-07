from django.db import migrations


RLS_POLICIES = [
    (
        "api_membership",
        "membership_tenant_isolation",
        "tenant_id::text = current_setting('app.tenant_id', true)",
    ),
    (
        "api_role",
        "role_tenant_isolation",
        "tenant_id::text = current_setting('app.tenant_id', true)",
    ),
]


def create_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table, policy, predicate in RLS_POLICIES:
            cursor.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
            cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            cursor.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            cursor.execute(
                f"""
                CREATE POLICY {policy}
                ON {table}
                USING ({predicate})
                WITH CHECK ({predicate})
                """
            )
        cursor.execute(
            "DROP POLICY IF EXISTS roleperm_tenant_isolation ON api_rolepermission"
        )
        cursor.execute(
            """
            ALTER TABLE api_rolepermission ENABLE ROW LEVEL SECURITY
            """
        )
        cursor.execute(
            """
            ALTER TABLE api_rolepermission FORCE ROW LEVEL SECURITY
            """
        )
        cursor.execute(
            """
            CREATE POLICY roleperm_tenant_isolation
            ON api_rolepermission
            USING (
                role_id IN (
                    SELECT id FROM api_role WHERE tenant_id::text = current_setting('app.tenant_id', true)
                )
            )
            WITH CHECK (
                role_id IN (
                    SELECT id FROM api_role WHERE tenant_id::text = current_setting('app.tenant_id', true)
                )
            )
            """
        )


def drop_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "DROP POLICY IF EXISTS roleperm_tenant_isolation ON api_rolepermission"
        )
        cursor.execute(
            """
            ALTER TABLE api_rolepermission NO FORCE ROW LEVEL SECURITY
            """
        )
        cursor.execute("ALTER TABLE api_rolepermission DISABLE ROW LEVEL SECURITY")
        for table, policy, _ in RLS_POLICIES:
            cursor.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
            cursor.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
            cursor.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_permission_role_tenant_and_more"),
    ]

    operations = [
        migrations.RunPython(create_rls, drop_rls),
    ]
