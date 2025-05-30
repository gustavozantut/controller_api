# KIPLACA/controller_api/alembic/env.py

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- Importações Específicas da Sua Aplicação ---
# O caminho 'app.db.database' funcionará porque o PYTHONPATH é configurado para
# incluir /controller_api (onde a pasta 'app' está)
from app.db.database import Base

# Importe TODOS os seus modelos SQLAlchemy para que o Alembic possa "vê-los"
# e compará-los com o banco de dados para a auto-geração.
from app.db.models import ApiKey  # <--- Importe seu modelo ApiKey

# Se você tiver outros modelos (ex: User), importe-os aqui também:
# from app.db.models import User

# Importe suas configurações da aplicação (onde está a DATABASE_URL)
from app.core.config import settings

# --- Configurações do Alembic ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata: Onde o Alembic encontra o esquema dos seus modelos
target_metadata = Base.metadata


# --- Funções de Migração ---
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    Configura o contexto apenas com a URL, sem conexão ao banco de dados.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    Cria uma conexão real com o banco de dados.
    """
    configuration = config.get_section(config.config_ini_section)
    # AQUI: O Alembic sobrescreve a URL do DB com a do seu settings.py.
    # A DATABASE_URL já deve ter o dialeto '+psycopg2'.
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# --- Ponto de Execução do Alembic ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
