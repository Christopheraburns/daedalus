from alembic import context
from sqlalchemy import create_engine

from factory.db import Base
from factory.settings import database_url

engine = create_engine(database_url())
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
