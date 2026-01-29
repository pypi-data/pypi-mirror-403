# Alembic migrations — Quick guide

Location
- Config and migrations: src/db/alembic/
- Generated migrations: src/db/alembic/versions/

Prerequisites
- Use the project Python environment and install deps: pip install -r src/requirements.txt
- Ensure the appropriate environment-specific database connection variable (e.g., LOCAL_DB, STAGING_DB, or PRODUCTION_DB as required by DatabaseConfig) is available via src/.env or system environment.
- Do not commit secrets.

***
***
***
***



Common commands (run from repo root)
- Create autogen revision:
    ``` alembic -c src/db/alembic/alembic.ini revision --autogenerate -m "short-msg" ```
- Review/edit generated file: src/db/alembic/versions/<timestamp>_*.py
- Generate SQL for review:
    ``` alembic -c src/db/alembic/alembic.ini upgrade --sql head > /tmp/migration.sql ```
- This lets you scroll up and down through the file. Press q to quit. : 
    ``` cat /tmp/migration.sql ```
- Apply migrations:
    ``` alembic -c src/db/alembic/alembic.ini upgrade head ```
- Inspect state:
-
    ```alembic -c src/db/alembic/alembic.ini current```
-
    ```alembic -c src/db/alembic/alembic.ini heads```
-
    ```alembic -c src/db/alembic/alembic.ini history --verbose```


***
***
***
***

How env.py works
- env.py adjusts PYTHONPATH to include project root and src, loads src/.env via python-dotenv, imports DatabaseConfig and db.schema.Base, and injects the SQLAlchemy URL into Alembic config at runtime.
- It also excludes ADK tables: sessions, events, app_states, user_states from autogeneration.



IMPORTANT NOTE:
If you want to get Back the schema and tables and the data
```pg_dump "YOUR_POSTGRES_CONNECTION_STRING" > prod_backup_with_data.sql``` 
and then execute the generated prod_backup_with_data.sql in sql editor of supabase
