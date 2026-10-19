"""Single-writer release reconciler and gateway supervisor."""

import json
import logging
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from .compiler import compile_bundle, digest
from .db import ApiOrigin, Release, Server, audit, database, now
from .gateway import candidate, gateway_config, materialize_secrets, start_executor, stop_process, validate_config, verify_effective, write_atomic
from .settings import LEGACY, MODERN, Settings
from .version import REVISION

log = logging.getLogger("factory.controller")


@dataclass
class Assets:
    """What a release needs beside the gateway config: its executor and secret files, in one directory."""
    directory: Path
    executor: object
    secrets: dict


def prepare_assets(bundle, settings, release_id):
    directory = settings.state_dir / "releases" / release_id
    directory.mkdir(parents=True, exist_ok=True)
    secrets = materialize_secrets(bundle, directory / "secrets")
    executor = None
    if bundle.get("python_tools"):
        (directory / "executor").mkdir(exist_ok=True)
        executor = start_executor(bundle, directory / "executor")
    return Assets(directory, executor, secrets)


def live_config(bundle, release_id, settings, assets):
    return gateway_config(bundle, release_id, settings, executor=assets.executor, secrets=assets.secrets, jwt=settings.jwt(), probe_port=settings.probe_port)


def retire_assets(assets):
    if assets:
        if assets.executor:
            stop_process(assets.executor.process)
        shutil.rmtree(assets.directory, ignore_errors=True)


LOCK = "SELECT pg_try_advisory_lock(hashtext(current_schema()), hashtext(:server_id))"
HOLDER = """SELECT a.application_name, host(a.client_addr) AS address, a.backend_start, a.pid FROM pg_locks l JOIN pg_stat_activity a ON a.pid = l.pid
    WHERE l.locktype = 'advisory' AND l.granted AND l.classid = (hashtext(current_schema())::bigint & 4294967295)::oid
    AND l.objid = (hashtext(:server_id)::bigint & 4294967295)::oid AND a.pid <> pg_backend_pid()"""


def describe_holder(owner, server_id):
    row = owner.execute(text(HOLDER), {"server_id": server_id}).mappings().first()
    if row is None:
        return "an unknown process"
    name = row["application_name"] or "a process without a name (an older Daedalus version or another client)"
    since = row["backend_start"].strftime("%Y-%m-%d %H:%M:%S %Z") if row["backend_start"] else "an unknown time"
    return f"{name} (from {row['address'] or 'a local socket'}, database pid {row['pid']}, connected since {since})"


def acquire_ownership(owner, server_id, wait, stopped):
    """One Server process per logical server. Wait a while for a previous copy to let go: during a
    Workbench restart the old pod can still hold the lock, or Postgres may not yet have noticed it is gone."""
    deadline = time.monotonic() + wait
    announced = 0.0
    while not owner.scalar(text(LOCK), {"server_id": server_id}):
        holder = describe_holder(owner, server_id)
        owner.commit()
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Another Server process owns MCP server {server_id}: {holder}. Stop that application, or wait for it to exit, then start this one again")
        if time.monotonic() - announced >= 10:
            log.warning("MCP server %s is owned by %s; waiting up to %d more seconds for it to exit", server_id, holder, int(deadline - time.monotonic()))
            announced = time.monotonic()
        if stopped.wait(2):
            raise RuntimeError("Stopped while waiting for ownership")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    server_id = settings.server_id
    identity = f"daedalus-server {server_id[:8]} on {socket.gethostname()}"
    engine, sessions = database(settings.database_url, identity)
    stopped = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopped.set())
    settings.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(settings.state_dir, 0o700)
    config_path = settings.state_dir / "gateway.json"
    empty = compile_bundle([], {}, settings.allowed_origins)
    process = assets = None
    # Connection-scoped lock prevents two Server instances writing the same server.
    with engine.connect() as owner:
        acquire_ownership(owner, server_id, float(os.getenv("FACTORY_LOCK_WAIT", "120")), stopped)
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
            approved = [row.origin for row in session.scalars(select(ApiOrigin).where(ApiOrigin.server_id == server_id, ApiOrigin.enabled.is_(True)))] or settings.allowed_origins
            compile_bundle(bundle["tools"], bundle["connections"], approved)
        started_at = now().isoformat()
        runtime = {"ready": False, "gateway_started_at": started_at, "effective_release_id": None, "last_error": None, "revision": REVISION, "host": socket.gethostname()}
        try:
            # The gateway fails closed on unreachable targets, so the executor is ready before it starts.
            assets = prepare_assets(bundle, settings, release_id)
            config = live_config(bundle, release_id, settings, assets)
            validate_config(config, settings, config_path)
            process = subprocess.Popen([settings.gateway_binary, "-f", str(config_path)], start_new_session=True)
            runtime["gateway_pid"] = process.pid
            runtime["executor_pid"] = assets.executor.process.pid if assets.executor else None
            with candidate(bundle, settings) as (_, _, expected):
                verify_effective(bundle, release_id, settings, process, expected, assets.executor)
            runtime.update(ready=True, effective_release_id=active.id if active else None, protocol_smoke_profiles=[MODERN, LEGACY])
            good_bundle, good_id = bundle, release_id
            good_catalog = expected
            last_check = time.monotonic()
            while not stopped.is_set():
                if process.poll() is not None:
                    raise RuntimeError("Gateway process exited; stopping Server for supervisor recovery")
                if assets.executor and assets.executor.process.poll() is not None:
                    raise RuntimeError("Executor process exited; stopping Server for supervisor recovery")
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
                        next_assets = None
                        try:
                            if digest(next_bundle) != checksum:
                                raise ValueError("Release checksum mismatch")
                            approved = [row.origin for row in session.scalars(select(ApiOrigin).where(ApiOrigin.server_id == server_id, ApiOrigin.enabled.is_(True)))] or settings.allowed_origins
                            compile_bundle(next_bundle["tools"], next_bundle["connections"], approved)
                            with candidate(next_bundle, settings) as (_, _, next_catalog):
                                # The previous executor keeps serving until the gateway has switched and verified.
                                next_assets = prepare_assets(next_bundle, settings, next_id)
                                config = live_config(next_bundle, next_id, settings, next_assets)
                                staged = settings.state_dir / "validated.json"
                                validate_config(config, settings, staged)
                                write_atomic(config_path, config)
                                verify_effective(next_bundle, next_id, settings, process, next_catalog, next_assets.executor)
                        except Exception as exc:
                            failure = str(exc)[:800].replace(settings.gateway_token, "[REDACTED]")
                            log.warning("Release %s failed: %s", next_id, failure)
                            retire_assets(next_assets)
                            # Preserve availability only if the previous release verifies again.
                            write_atomic(config_path, live_config(good_bundle, good_id, settings, assets))
                            verify_effective(good_bundle, good_id, settings, process, good_catalog, assets.executor)
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
                                retire_assets(assets)
                                assets = next_assets
                                runtime.update(effective_release_id=next_id, last_error=None, executor_pid=assets.executor.process.pid if assets.executor else None)
                                # Durable authoritative copy is PostgreSQL; this is a local recovery artifact.
                                write_atomic(settings.state_dir / "last-known-good.json", {"release_id": next_id, "checksum": checksum, "bundle": next_bundle})
                                audit(session, "controller", "release.active", next_id, gateway_pid=process.pid, checksum=checksum)
                            server.revision += 1
                            runtime["heartbeat"] = now().isoformat()
                            server.runtime = dict(runtime)
                        log.info("Release %s %s; gateway PID %s", next_id, "failed" if failure else "active", process.pid)
                    # Detect config drift, including changes through the private upstream UI.
                    if time.monotonic() - last_check > 10:
                        expected_config = live_config(good_bundle, good_id, settings, assets)
                        if json.loads(config_path.read_text()) != expected_config:
                            raise RuntimeError("Gateway configuration drift detected")
                        verify_effective(good_bundle, good_id, settings, process, good_catalog, assets.executor)
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
            retire_assets(assets)
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
