import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Mesmas env vars PG* usadas por app/database/db.py e app/__init__.py —
# respeita TEST_PGDATABASE, mesma convenção de tests/conftest.py (ADR-001).
load_dotenv()


def _sqlalchemy_url():
    usuario = quote_plus(os.getenv("PGUSER", "postgres"))
    senha = quote_plus(os.getenv("PGPASSWORD", "postgres"))
    host = os.getenv("PGHOST", "localhost")
    porta = os.getenv("PGPORT", "5432")
    banco = os.getenv("TEST_PGDATABASE") or os.getenv("PGDATABASE", "expense_management")
    return f"postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{banco}"


# Não usamos config.set_main_option("sqlalchemy.url", ...) porque o configparser
# interpreta "%" como início de interpolação — senhas com caracteres especiais
# (ex.: "*", "#" percent-encoded) quebram isso. A URL é usada diretamente abaixo,
# fora do configparser.
DATABASE_URL = _sqlalchemy_url()

# Metadados dos models ORM (Tarefa 3.1) para suportar autogenerate.
from app import models  # noqa: E402
from app.extensions import db  # noqa: E402

target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
