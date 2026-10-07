"""Restart only the isolated acceptance project and compare its persisted workspace."""
import json
from pathlib import Path
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    environment = dict(line.split("=", 1) for line in (root / ".env").read_text().splitlines() if line and not line.startswith("#"))
    token = environment["FACTORY_ADMINISTRATOR_TOKEN"]
    command = ["docker", "compose", "-p", "daedalus-checks", "--env-file", ".env", "--env-file", "tests/ports.env"]

    def workspace():
        request = Request("http://127.0.0.1:18000/api/workspace", headers={"Authorization": "Bearer " + token})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def persisted(value):
        return {key: value[key] for key in ("connections", "tools", "layout", "active_tools", "releases")} | {
            "server": {key: value["server"][key] for key in ("id", "name", "revision", "active_release_id", "desired_release_id")}
        }

    before = workspace()
    assert before["tools"] and before["layout"]["positions"] and before["server"]["active_release_id"], "Run browser acceptance first"
    subprocess.run(command + ["down"], cwd=root, check=True)
    subprocess.run(command + ["up", "-d"], cwd=root, check=True)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            after = workspace()
            runtime = after["server"]["runtime"]
            if runtime.get("ready") and runtime.get("online") and runtime.get("gateway_started_at") != before["server"]["runtime"].get("gateway_started_at"):
                assert persisted(before) == persisted(after), "Persisted workspace changed across restart"
                print("PASS: connections, drafts, test evidence, layout, releases, and active snapshot survived Docker recreation.")
                return
        except (URLError, TimeoutError):
            pass
        time.sleep(0.5)
    raise AssertionError("Runtime did not recover after Docker recreation")


if __name__ == "__main__":
    main()
