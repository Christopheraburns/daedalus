# MCP Factory development runtime

This image supplies the development environment described in section 4 of
[the developer plan](../MCP_Factory_Developer_Plan.md). It includes standalone
agentgateway, Node.js/npm, an isolated Python environment, PostgreSQL client
libraries, Git, build tools, pytest, and Ruff. The Python lock includes FastAPI,
Uvicorn, validation, database migrations, JWT/cryptography, OpenTelemetry, and a
candidate MCP SDK for feasibility testing.

The Builder, Server, release reconciler, authentication, and project launchers
remain application work. Building or registering this runtime does not create
those applications or establish MCP protocol conformance.

## Selected base

The Dockerfile defaults to the selected Cloudera runtime:

```text
docker.repository.cloudera.com/cloudera/cdsw/ml-runtime-pbj-workbench-python3.12-standard:2026.08.1-b5
sha256:106220420aa35e733fe362a07a0f14af11d2d27f58aa527fa13d931598ef7262
```

The tag and immutable digest are both recorded in `BASE_IMAGE`. No build argument
is needed for this base. Authenticate to the Cloudera registry first if required.
The build checks the digest format, amd64 architecture, Python 3.12, Ubuntu OS,
Cloudera editor metadata, and `cdsw` UID/GID. To change bases, supply
`--build-arg BASE_IMAGE=REPOSITORY@sha256:DIGEST` and rerun validation; other Python
or architecture profiles also require a lockfile refresh.

## Build and verify

Run from the repository root. Replace the destination registry/namespace:

```sh
export IMAGE='YOUR_REGISTRY/YOUR_NAMESPACE/mcp-factory-runtime:0.1.1'

docker build --platform linux/amd64 \
  -f runtime/Dockerfile -t "$IMAGE" .

docker run --rm --platform linux/amd64 \
  --entrypoint /opt/mcp-factory/venv/bin/python \
  "$IMAGE" /opt/mcp-factory/smoke_check.py

docker image inspect "$IMAGE" --format '{{json .Config.Labels}}'
```

Use Docker BuildKit. The explicit platform also applies when building on an
Apple Silicon Mac. The smoke check runs as `cdsw` during the build and verifies
imports, a FastAPI request, and execution of agentgateway, Node.js, npm, and Ruff.
It does not test PostgreSQL connectivity, gateway routing, or Workbench ingress.

The build preserves the base editor, Python/Jupyter configuration, metadata
version, working directory, and startup command. Custom edition/version metadata
is set in both labels and environment variables. Do not add an application
`ENTRYPOINT`, replace the platform Python, or install into `/home/cdsw`: Cloudera
mounts project storage there.

## Push and register in Cloudera

```sh
docker login YOUR_REGISTRY
docker push "$IMAGE"
```

1. Ensure Workbench workers can pull the image. Configure private registry
   credentials and certificates in Cloudera when necessary.
2. As a Cloudera administrator, open **Runtime Catalog → Add Runtime**, enter the
   pushed image URL, and select **Validate**. Complete registration after it passes.
3. Create/open the MCP Factory project and select **MCP Factory Development**,
   version **0.1**, maintenance **1**, with the inherited Python 3.12 editor.
4. Upload or clone this repository into the project and start a session. In its
   terminal run `mcp-factory-python /opt/mcp-factory/smoke_check.py`.
5. Record the Workbench version, pushed runtime digest, and
   validation results in [compatibility.yaml](../compatibility.yaml).

For a PBJ code cell, run the smoke check as a subprocess so it uses the isolated
Factory environment:

```python
import subprocess
subprocess.run([
    "/opt/mcp-factory/venv/bin/python",
    "/opt/mcp-factory/smoke_check.py",
], check=True)
```

Cloudera's registration and metadata requirements are documented in
[Adding the new ML Runtime](https://docs.cloudera.com/machine-learning/1.5.4/runtimes/topics/ml-registering-customized-runtimes.html)
and [custom runtime metadata](https://docs.cloudera.com/machine-learning/1.5.4/runtimes/topics/ml-metadata-for-custom-runtimes.html).
Check these against your deployed release.

## Develop in the project

The editor continues to use Cloudera's Python. Run application code with
`mcp-factory-python` or `/opt/mcp-factory/venv/bin/python`; global `python` and
`pip` intentionally keep their original meaning. Node.js and agentgateway are
on `PATH`. React and TypeScript will be project dependencies locked by the UI's
future `package-lock.json`, rather than global npm installs.

The image environment is read-only to `cdsw`. To experiment with additional
Python packages in persistent project storage:

```sh
mcp-factory-python -m venv .venv
PIP_CONFIG_FILE=/dev/null PIP_USER=false .venv/bin/python -m pip install \
  --require-hashes --only-binary=:all: -r runtime/requirements.lock
PIP_CONFIG_FILE=/dev/null PIP_USER=false .venv/bin/python -m pip install YOUR_PACKAGE
```

Promote dependencies needed by everyone into `requirements.in`, refresh the lock,
and rebuild. Do not put credentials in build arguments, the Dockerfile, or source.

When application launchers are implemented, they must use the Factory interpreter,
read `CDSW_APP_PORT` at launch, bind to the address required by the target
Workbench, and supervise their children. Never hard-code the application port.
Cloudera documents loopback binding for
[application services](https://docs.cloudera.com/machine-learning/1.5.5/engines/topics/ml-engine-environment-variables.html);
verify it on the selected release. Gateway administration and adapters must stay
private. Put persistent configuration in the project or external PostgreSQL.

## Update and qualify

Refresh the Python lock using `uv` (initial lock generated with 0.7.3):

```sh
uv pip compile runtime/requirements.in --upgrade \
  --python-version 3.12 --python-platform x86_64-manylinux_2_28 \
  --generate-hashes --only-binary :all: --no-python-downloads \
  --output-file runtime/requirements.lock
```

All resolved Python dependencies are pinned with hashes. agentgateway **1.6.0**
and Node.js **22.23.3** have pinned SHA-256 values in the Dockerfile, obtained from
the [agentgateway release API](https://api.github.com/repos/agentgateway/agentgateway/releases/tags/v1.6.0)
and [Node release checksums](https://nodejs.org/download/release/v22.23.3/SHASUMS256.txt).
Change version and checksum together, refresh the bundled gateway license when
upgrading it, and rerun compatibility checks. Ubuntu packages come from configured
apt repositories; a frozen apt mirror is needed for byte-for-byte rebuilds.

Increment `RUNTIME_MAINTENANCE_VERSION` for replacement builds:

```sh
docker build --platform linux/amd64 \
  --build-arg RUNTIME_MAINTENANCE_VERSION=2 \
  -f runtime/Dockerfile -t YOUR_REGISTRY/YOUR_NAMESPACE/mcp-factory-runtime:0.1.2 .
```

Retain the previous image digest for rollback. Before promoting an image, generate
an SBOM and vulnerability report using your organization's scanner; for example,
with Syft and Grype installed on the build machine:

```sh
mkdir -p artifacts
syft "$IMAGE" -o spdx-json > artifacts/runtime.spdx.json
grype "$IMAGE" -o json > artifacts/runtime-vulnerabilities.json
```

The image includes Python package inventory at
`/opt/mcp-factory/python-packages.json`, gateway licensing under
`/opt/mcp-factory/licenses`, and Node's upstream `LICENSE` under
`/opt/mcp-factory/node`. Package inventories are not a complete image SBOM.
Complete the plan's real Workbench ingress, protocol, auth, reload, and persistence
gates before declaring production support.

## Local validation evidence

On 2026-10-06, the image built and its smoke check passed using the selected
Cloudera `2026.08.1-b5` base and digest recorded above. The base has Ubuntu 24.04,
Python 3.12.13, amd64, and PBJ Workbench metadata. Python dependency consistency,
imports, a FastAPI request, and agentgateway/Node.js/npm/Ruff execution passed as
`cdsw`. The resulting local image is `mcp-factory-runtime:0.1.1`, image ID
`sha256:f6cc950e864096c965c9667d4edbe4ecce3ab42b2fc772efd7f9edaddc030b53`.
This is a local Docker image ID, not a pushed registry manifest digest.
Cloudera registration and actual Workbench ingress validation remain pending.

To publish this already-built image instead of rebuilding it, set `IMAGE` to your
destination as above, then run:

```sh
docker tag mcp-factory-runtime:0.1.1 "$IMAGE"
docker push "$IMAGE"
```
