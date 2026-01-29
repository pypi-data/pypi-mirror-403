from __future__ import with_statement
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------
# Fix PYTHONPATH (root + src)
# ---------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ---------------------------------------
# Load .env from src/
# ---------------------------------------

from dotenv import load_dotenv
ENV_PATH = os.path.join(SRC_DIR, ".env")
load_dotenv(ENV_PATH)

# ---------------------------------------
# Import Base models
# ---------------------------------------

from db.schema import Base

# Alembic setup
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject DB URL dynamically
try:
    db_url = os.getenv('WOWBITS_DB_CONNECTION_STRING')
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)
    else:
        print("WARNING: WOWBITS_DB_CONNECTION_STRING not found in environment")
except Exception as e:
    print("WARNING: Could not load database connection string:", e)

# Autogeneration metadata
target_metadata = Base.metadata

# Exclude ADK tables
def include_object(object, name, type_, reflected, compare_to):
    EXCLUDED = {"sessions", "events", "app_states", "user_states"}
    if type_ == "table" and name in EXCLUDED:
        return False
    return True


# ---------------------------------------
# Migration runners
# ---------------------------------------

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
