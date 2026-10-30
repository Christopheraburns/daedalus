from alembic import command
from alembic.config import Config

from . import packstore
from .db import ApiOrigin, Deployment, Layout, Server, database
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
            for origin in settings.allowed_origins:
                if origin:
                    session.add(ApiOrigin(server_id=SERVER_ID, origin=origin, description="Environment bootstrap origin"))
        # Packs that earlier versions kept as files in project storage move into the registry once.
        moved = packstore.import_legacy_files(session, settings)
        if moved:
            print(f"Imported project packs from {packstore.packs.project_dir()}: {', '.join(moved)}")
    engine.dispose()


if __name__ == "__main__":
    main()
