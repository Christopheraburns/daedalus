"""Where tool packs come from, and what the Builder knows about them.

Three origins, one source of truth:

- *built-in* packs ship in the code (`factory.packs`) and are read-only;
- *seed* packs ship in the code too (`factory/seedpacks`) but do nothing until enabled, either by
  FACTORY_PACKS_ENABLED on the application or by an administrator's toggle stored in `pack_settings`.
  Editing a seed copies it into the `packs` table as a project pack that shadows the seed;
- *project* packs live in the `packs` table, written from the Builder.

What a pack contains (tools, parameters, docstrings) is found by importing its code in a subprocess,
and the result is cached in `pack_inspections` by source digest: one subprocess per distinct source,
not one per request. Nothing in this module writes to the filesystem, so a Builder restarted on a new
host sees exactly the packs it had before.
"""
from sqlalchemy import select

from . import packs
from .db import Pack, PackInspection, PackSetting, audit


def inspection(session, name, source):
    digest = packs.digest_of(source)
    cached = session.get(PackInspection, digest)
    if cached is not None:
        return cached.result
    result = packs.inspect_source(name, source)
    session.merge(PackInspection(digest=digest, result=result))
    session.flush()
    return result


def settings_rows(session):
    return {row.name: row for row in session.scalars(select(PackSetting))}


def seed_enabled(session, settings, name, rows=None):
    rows = settings_rows(session) if rows is None else rows
    return rows[name].enabled if name in rows else name in settings.packs_enabled


def trim(entry, include_source):
    if not include_source:
        entry.pop("source", None)
        for tool in [*entry["tools"], *([entry["probe"]] if entry.get("probe") else [])]:
            tool.pop("source", None)
    return entry


def described(name, origin, source, inspected, **extra):
    return {"name": name, "origin": origin, "error": inspected.get("error"), "description": inspected.get("description", ""),
        "protocol": inspected.get("protocol", "rest"), "tools": inspected.get("tools", []), "probe": inspected.get("probe"), "source": source, **extra}


def entry(session, settings, name, include_source=False):
    """One pack as the Builder sees it. Unknown names and seeds that are not enabled raise ValueError."""
    if name in packs.builtin_names():
        return trim(packs.builtin_info(name), include_source)
    row = session.get(Pack, name)
    if row is not None:
        extra = {"editable": True, "revision": row.revision}
        if name in packs.seed_names():
            extra.update(forked_from_seed=True, seed_updated=row.forked_from_digest != packs.digest_of(packs.seed_source(name)))
        return trim(described(name, "project", row.source, inspection(session, name, row.source), **extra), include_source)
    if name in packs.seed_names():
        if not seed_enabled(session, settings, name):
            raise ValueError(f"Unknown tool pack: {name} (a seed pack that is not enabled)")
        source = packs.seed_source(name)
        return trim(described(name, "seed", source, inspection(session, name, source), editable=True, enabled=True), include_source)
    raise ValueError(f"Unknown tool pack: {name}")


def catalog(session, settings, include_source=False):
    """Built-in packs, then enabled seeds (unless a project pack shadows them), then project packs."""
    rows = settings_rows(session)
    projects = [p.name for p in session.scalars(select(Pack).order_by(Pack.name))]
    seeds = [n for n in packs.seed_names() if n not in projects and seed_enabled(session, settings, n, rows)]
    return [entry(session, settings, n, include_source) for n in [*packs.builtin_names(), *seeds, *projects]]


def seeds(session, settings):
    """Every seed pack with its state, for the administrator's pack settings."""
    rows = settings_rows(session)
    result = []
    for name in packs.seed_names():
        source = packs.seed_source(name)
        inspected = inspection(session, name, source)
        row = session.get(Pack, name)
        result.append({"name": name, "enabled": seed_enabled(session, settings, name, rows),
            "configured_by": "setting" if name in rows else ("environment" if name in settings.packs_enabled else "default"),
            "description": inspected.get("description", ""), "protocol": inspected.get("protocol", "rest"), "error": inspected.get("error"),
            "tools": len(inspected.get("tools", [])), "shadowed": row is not None,
            "seed_updated": row is not None and row.forked_from_digest != packs.digest_of(source)})
    return result


def set_enabled(session, settings, name, enabled, actor):
    if name not in packs.seed_names():
        raise ValueError(f"{name} is not a seed pack")
    row = session.get(PackSetting, name) or PackSetting(name=name)
    row.enabled, row.updated_by = enabled, actor
    session.add(row)
    audit(session, actor, "pack.enable" if enabled else "pack.disable", f"pack:{name}")


def save(session, settings, name, source, actor):
    """Validate and store a project pack. Saving under a seed's name forks the seed."""
    inspected = packs.check_source(name, source)
    row = session.get(Pack, name)
    if row is None:
        row = Pack(name=name, forked_from_digest=packs.digest_of(packs.seed_source(name)) if name in packs.seed_names() else None)
        session.add(row)
    else:
        row.revision += 1
    row.source, row.digest, row.updated_by = source, packs.digest_of(source), actor
    session.merge(PackInspection(digest=row.digest, result=inspected))
    session.flush()
    return entry(session, settings, name, include_source=True)


def delete(session, name):
    row = session.get(Pack, name)
    if row is None:
        raise ValueError("Only project packs can be deleted")
    session.delete(row)


def source_of(session, settings, name):
    """Source of a pack that is not built in (None for built-ins). A seed that is not enabled is unknown."""
    if name in packs.builtin_names():
        return None
    row = session.get(Pack, name)
    if row is not None:
        return row.source
    if name in packs.seed_names() and seed_enabled(session, settings, name):
        return packs.seed_source(name)
    raise ValueError(f"Unknown tool pack: {name}")


def sources(session, settings):
    """Every available non-built-in pack's source by name: what releases snapshot from."""
    rows = settings_rows(session)
    result = {p.name: p.source for p in session.scalars(select(Pack))}
    for name in packs.seed_names():
        if name not in result and seed_enabled(session, settings, name, rows):
            result[name] = packs.seed_source(name)
    return result


def pack_digest(session, settings, name):
    """Digest of the pack code a tool would run with; editing a pack changes it and so invalidates test evidence."""
    try:
        source = source_of(session, settings, name)
    except ValueError:
        return None
    return packs.digest_of(source) if source is not None else None


def lookup(entries):
    """A session-free tool lookup over pre-read pack entries: safe to call after the session's block has ended."""
    def tool_info(pack, function):
        if pack in packs.builtin_names():
            return packs.builtin_tool_info(pack, function)
        if pack not in entries:
            raise ValueError(f"Unknown tool pack: {pack}" + (" (a seed pack that is not enabled)" if pack in packs.seed_names() else ""))
        return packs.find_tool(entries[pack], pack, function)
    return tool_info


def resolver(session, settings):
    """Tool lookup for the Builder: built-ins, enabled seeds and project packs, all read now."""
    return lookup({e["name"]: e for e in catalog(session, settings) if e["origin"] != "builtin"})


def resolver_from_sources(session, pack_sources):
    """Tool lookup for a release bundle: built-ins from the code, everything else from the bundle's own snapshot."""
    return lookup({name: described(name, "snapshot", None, inspection(session, name, source)) for name, source in pack_sources.items()})


def view(session, settings):
    """(resolver, sources) for compile_bundle, read in one go while the session is open."""
    return resolver(session, settings), sources(session, settings)


def probes(session, settings, protocol):
    """Packs that can check a connection of this protocol: [(pack name, probe description)]."""
    return [(e["name"], e["probe"]["description"]) for e in catalog(session, settings) if e.get("probe") and e["protocol"] == protocol and not e.get("error")]


def import_legacy_files(session, settings, log=print):
    """One-time move of packs that earlier versions stored as files under FACTORY_PACKS_DIR into the registry."""
    directory = packs.project_dir()
    if not directory.is_dir():
        return []
    moved = []
    for path in sorted(directory.glob("*.py")):
        name = path.stem
        if not packs.PACK_NAME.match(name) or name in packs.builtin_names() or session.get(Pack, name) is not None:
            continue
        try:
            save(session, settings, name, path.read_text(), "migration")
            moved.append(name)
        except (ValueError, SyntaxError) as exc:
            log(f"Pack file {path} was not imported: {exc}")
    return moved
