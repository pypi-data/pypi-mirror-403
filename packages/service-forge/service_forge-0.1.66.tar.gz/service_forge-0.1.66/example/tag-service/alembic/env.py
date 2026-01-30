import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from dotenv import load_dotenv

from service_forge.sft.config.sf_metadata import load_metadata
from service_forge.db.database import DatabaseManager

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

metadata = load_metadata("./sf-meta.yaml")

database = DatabaseManager.from_config(config_path=metadata.service_config)
url = database.get_default_postgres_database().database_url

config.set_main_option("sqlalchemy.url", url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import all models to ensure they are registered with Base.metadata
import sys
import importlib
import inspect
from pathlib import Path

# Add the project root to the path so we can import models
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import Base first
from model.db import Base

def import_all_base_models():
    db_path = Path(__file__).resolve().parents[1] / "model" / "db"
    
    for file_path in sorted(db_path.glob("*.py")):
        if file_path.name == "__init__.py":
            continue
        
        module_name = file_path.stem
        try:
            print(f"Importing module: model.db.{module_name}")
            module = importlib.import_module(f"model.db.{module_name}")
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, Base) and 
                    obj is not Base and
                    obj.__module__ == module.__name__):
                    if hasattr(obj, '__table__'):
                        _ = obj.__table__
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to import model.db.{module_name}: {e}")

import_all_base_models()

# Set target_metadata for autogenerate support
target_metadata = Base.metadata

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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    
    # Check if we have a connection provided via the attributes (from programmatic use)
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        # No connection provided, run async migrations
        asyncio.run(run_async_migrations())
    else:
        # Connection provided programmatically, use it directly
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()