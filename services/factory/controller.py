"""Single-writer release reconciler and gateway supervisor."""

import json
import logging
import os
import signal
import subprocess
import threading
import time

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from .compiler import compile_bundle, digest
from .db import Release, Server, audit, database, now
from .gateway import candidate, gateway_config, stop_process, validate_config, verify_effective, write_atomic
from .settings import LEGACY, MODERN, Settings

log = logging.getLogger("factory.controller")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    server_id = settings.server_id
    engine, sessions = database(settings.database_url)
    stopped = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopped.set())
    settings.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(settings.state_dir, 0o700)
    config_path = settings.state_dir / "gateway.json"
    empty = compile_bundle([], {}, settings.allowed_origins)
    process = None
    # Connection-scoped lock prevents two Server instances writing the same server.
    with engine.connect() as owner:
        if not owner.scalar(text("SELECT pg_try_advisory_lock(hashtext(current_schema()), hashtext(:server_id))"), {"server_id": server_id}):
            raise RuntimeError("Another Server process owns this logical MCP server")
        with sessions() as session:
            server = session.get(Server, server_id)
            if server is None:
                raise RuntimeError("Run registry migrations before launching Server")
            requested_release = settings.deployed_release_id or server.active_release_id
            active = session.get(Release, requested_release) if requested_release else None
            if active and active.server_id != server_id:
                raise RuntimeError("Requested release belongs to a different MCP server")
            bundle, release_id = (active.bundle, active.id) if active else (empty, "empty")
            if active and digest(bundle) != active.checksum:
                raise RuntimeError("Last active release failed integrity verification")
            # Revalidate approved origins at every startup, including saved releases.
            compile_bundle(bundle["tools"], bundle["connections"], settings.allowed_origins)
        config = gateway_config(bundle, release_id, settings)
        validate_config(config, settings, config_path)
        started_at = now().isoformat()
        runtime = {"ready": False, "gateway_started_at": started_at, "effective_release_id": None, "last_error": None}
        try:
            process = subprocess.Popen([settings.gateway_binary, "-f", str(config_path)], start_new_session=True)
            runtime["gateway_pid"] = process.pid
            with candidate(bundle, settings) as (_, _, expected):
                verify_effective(bundle, release_id, settings, process, expected)
            runtime.update(ready=True, effective_release_id=active.id if active else None, protocol_smoke_profiles=[MODERN, LEGACY])
            good_bundle, good_id = bundle, release_id
            good_catalog = expected
            last_check = time.monotonic()
            while not stopped.is_set():
                if process.poll() is not None:
                    raise RuntimeError("Gateway process exited; stopping Server for supervisor recovery")
                try:
                    # A lost advisory-lock connection must terminate ownership too.
                    owner.execute(text("SELECT 1"))
                    with sessions.begin() as session:
                        server = session.scalar(select(Server).where(Server.id == server_id).with_for_update())
                        runtime["heartbeat"] = now().isoformat()
                        server.runtime = dict(runtime)
                        desired = session.get(Release, server.desired_release_id) if server.desired_release_id else None
                        pending = not settings.deployed_release_id and desired is not None and desired.status in {"pending", "applying"}
                        if pending:
                            desired.status = "applying"
                            next_bundle, next_id, checksum = desired.bundle, desired.id, desired.checksum
                    if pending:
                        failure = None
                        try:
                            if digest(next_bundle) != checksum:
                                raise ValueError("Release checksum mismatch")
                            compile_bundle(next_bundle["tools"], next_bundle["connections"], settings.allowed_origins)
                            with candidate(next_bundle, settings) as (_, _, next_catalog):
                                config = gateway_config(next_bundle, next_id, settings)
                                staged = settings.state_dir / "validated.json"
                                validate_config(config, settings, staged)
                                write_atomic(config_path, config)
                                verify_effective(next_bundle, next_id, settings, process, next_catalog)
                        except Exception as exc:
                            failure = str(exc)[:800].replace(settings.gateway_token, "[REDACTED]")
                            log.warning("Release %s failed: %s", next_id, failure)
                            # Preserve availability only if the previous release verifies again.
                            write_atomic(config_path, gateway_config(good_bundle, good_id, settings))
                            verify_effective(good_bundle, good_id, settings, process, good_catalog)
                        with sessions.begin() as session:
                            server = session.scalar(select(Server).where(Server.id == server_id).with_for_update())
                            release = session.get(Release, next_id)
                            release.error = failure
                            if failure:
                                release.status = "failed"
                                runtime["last_error"] = failure
                                audit(session, "controller", "release.failed", next_id, recovered_release_id=server.active_release_id)
                            else:
                                previous = session.get(Release, server.active_release_id) if server.active_release_id else None
                                if previous and previous.id != next_id:
                                    previous.status = "superseded"
                                release.status = "active"
                                server.active_release_id = next_id
                                good_bundle, good_id, good_catalog = next_bundle, next_id, next_catalog
                                runtime.update(effective_release_id=next_id, last_error=None)
                                # Durable authoritative copy is PostgreSQL; this is a local recovery artifact.
                                write_atomic(settings.state_dir / "last-known-good.json", {"release_id": next_id, "checksum": checksum, "bundle": next_bundle})
                                audit(session, "controller", "release.active", next_id, gateway_pid=process.pid, checksum=checksum)
                            server.revision += 1
                            runtime["heartbeat"] = now().isoformat()
                            server.runtime = dict(runtime)
                        log.info("Release %s %s; gateway PID %s", next_id, "failed" if failure else "active", process.pid)
                    # Detect config drift, including changes through the private upstream UI.
                    if time.monotonic() - last_check > 10:
                        expected_config = gateway_config(good_bundle, good_id, settings)
                        if json.loads(config_path.read_text()) != expected_config:
                            raise RuntimeError("Gateway configuration drift detected")
                        verify_effective(good_bundle, good_id, settings, process, good_catalog)
                        last_check = time.monotonic()
                except SQLAlchemyError:
                    # Keep serving the last verified release while the registry recovers.
                    log.warning("Registry unavailable; retaining last verified release")
                    # Do not keep running without the ownership lock.
                    if owner.invalidated:
                        raise RuntimeError("Registry ownership connection lost; stopping Server")
                stopped.wait(1)
        finally:
            if process:
                stop_process(process)
            try:
                with sessions.begin() as session:
                    server = session.get(Server, server_id)
                    if server:
                        runtime.update(ready=False, heartbeat=now().isoformat())
                        server.runtime = runtime
            except SQLAlchemyError:
                pass
            engine.dispose()


if __name__ == "__main__":
    main()
