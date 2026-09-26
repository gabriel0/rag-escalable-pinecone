# pythonLibFunctions

Utilidades para pipelines de librerias Python.

Soporta:

- `pyproject.toml` (PEP 621 / setuptools / hatchling / flit)
- `setup.py` / `setup.cfg`
- Poetry (`poetry.lock` o `[tool.poetry]`)

## Backend

- `poetry`: si hay `poetry.lock` o `[tool.poetry]`, o `PYTHON_BUILD_TOOL=poetry`
- `build`: `python -m build` + `twine` (default)

## Fases (`python-lib.sh`)

| Fase | Accion |
|---|---|
| install | poetry install o `pip install -e .[dev]` |
| build | `poetry build` o `python -m build` |
| test | pytest (se omite si no esta disponible) |
| publish | `twine upload` al hosted Nexus |

## Snapshot / release

- **develop** → `{app}_pypi_hosted_snapshot` (republicable)
- **tag release-x.y.z** → `{app}_pypi_hosted` (sin redeploy)
- En develop se recomienda version PEP 440 `.devN` (ej. `1.2.3.dev0`); no se fuerza

## Variables utiles

| Variable | Descripcion |
|---|---|
| `LANG_VERSION` | Tag Python (`3.10`..`3.14`). Default `3.12` |
| `PYTHON_IMAGE_VARIANT` | `slim` → `docker-agents/python:X.Y-slim` |
| `DOCKER_IMAGE` | Override completo de imagen |
| `PYTHON_BUILD_TOOL` | `poetry` o `build` |
| `PYPI_HOSTED_REPOSITORY` / `_SNAPSHOT` / `PYPI_PROXY_REPOSITORY` | Override nombres Nexus |

## Metodos

### materializeScripts(Map params = [:])

Copia `resources/python/setup-pip-conf.sh` y `python-lib.sh` al workspace y les da `chmod +x`.

- `targetDir`: default `application`.

No retorna valor.

### detectBackend(String workDir)

Retorna el backend de build:

1. `env.PYTHON_BUILD_TOOL` si esta definido.
2. `poetry` si existe `poetry.lock` o `pyproject.toml` con `[tool.poetry]`.
3. `build` en cualquier otro caso.

### readProjectMetadata(String workDir)

Lee `name` y `version`. Orden: `[project]` de `pyproject.toml` (PEP 621), `[tool.poetry]`, cualquier `name`/`version`, luego `setup.cfg` `[metadata]`, luego `setup.py`.

Retorna `[name, version]`. Sin nombre usa `env.SERVICE_NAME`. Sin version usa `0.0.0`.

### normalizePyPiName(String packageName)

Pasa el nombre a minusculas y cambia `_` por `-`. Retorna null si la entrada es null.

### detectPythonVersion(String workDir)

1. `env.LANG_VERSION`.
2. Major.minor de `.python-version`.
3. Primer `X.Y` de `requires-python` en `pyproject.toml`.
4. `3.12`.

### resolveDockerImage(String dockerRegistry, String langVersion)

Retorna `{dockerRegistry}/docker-agents/python:{langVersion}`. Si `PYTHON_IMAGE_VARIANT=slim`, el tag es `{langVersion}-slim`.

### validatePythonRedeployAllowed(String workDir)

Solo corre en `LIB_PUBLICATION_TYPE=release`. Consulta `{LIB_REPOSITORY_URL}/packages/{nombre}/{version}/` con la credencial `NEXUS_CREDENTIAL_ID`.

HTTP `200`, `301` o `302` aborta: el paquete ya existe en retain. Otro codigo se loguea como OK. En snapshot no valida.

Sin nombre o version, aborta con `error`.

### initializeLibEnv(Map params = [:])

- `workDir`: default `application`.
- `dockerRegistry`: default `env.DOCKERREGISTRY` o `registry.example.com:8083`.

Exige `LIB_PUBLICATION_TYPE` (`snapshot` o `release`) y un manifest (`pyproject.toml`, `setup.py` o `setup.cfg`).

Setea `PACKAGE_NAME`, `VERSION`, `PYTHON_BUILD_TOOL`, `LANG_VERSION`, repos Nexus via `libBuildFunctions.configureNexusRepositories('pypi')` y `DOCKER_IMAGE` si no venia definida.

En snapshot, si la version es `X.Y.Z` sin sufijo developmental, loguea advertencia y sigue. No retorna valor.

### runPhase(String phase, Map params = [:])

Ejecuta `./python-lib.sh {phase}` dentro de `DOCKER_IMAGE`.

- `phase`: `install`, `build`, `test` o `publish`.
- `workDir`: default `application`.
- `dockerImage`: default `env.DOCKER_IMAGE`.
- `credentialsId`: default `env.NEXUS_CREDENTIAL_ID`.

`publish` llama antes a `validatePythonRedeployAllowed`. Imagen vacia o que termina en `:` aborta.

Monta `${WORKSPACE}/.cache` en `/root/.cache` y corre como root. Al salir hace `chown` al owner del workspace. No retorna valor.
