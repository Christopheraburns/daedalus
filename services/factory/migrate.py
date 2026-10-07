from alembic import command
from alembic.config import Config

from .db import Deployment, Layout, Server, database
from .settings import ROOT, SERVER_ID, Settings


def main():
    settings = Settings()
    command.upgrade(Config(str(ROOT / "services/alembic.ini")), "head")
    engine, sessions = database(settings.database_url)
    with sessions.begin() as session:
        if not session.get(Server, SERVER_ID):
            session.add(Server(id=SERVER_ID))
            session.flush()
            session.add(Layout(server_id=SERVER_ID))
            session.add(Deployment(server_id=SERVER_ID))
    engine.dispose()


if __name__ == "__main__":
    main()
