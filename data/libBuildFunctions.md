# libBuildFunctions

Fachada comun para pipelines de librerias Java, NPM y Python.

El objetivo es mantener los Jenkinsfiles simples y declarativos, dejando la deteccion del stack y la delegacion de fases en la libreria compartida.

## Estrategia de publicacion

La estrategia de origen la define `gitFunctions.checkoutLibrarySourceFromEvent`:

- Commits en `develop`: publican snapshots.
- Tags `release-*`: publican releases en retain.
- El tag `release-x.y.z` debe crearse sobre la rama `releases` o, si esa no existe, `release/x.y.z`.

`libBuildFunctions` consume `env.LIB_PUBLICATION_TYPE` para que Java/NPM/Python inicialicen el repositorio Nexus correcto.

Validacion de version segun stack:

- Java: en `develop` exige sufijo `-SNAPSHOT`; en release la version del proyecto debe coincidir con el tag y no ser SNAPSHOT.
- NPM: en `develop` no exige sufijo `-SNAPSHOT` en `package.json`; en release la version debe coincidir con el tag.
- Python: en `develop` publica al hosted snapshot y recomienda version PEP 440 developmental (ej. `1.2.3.dev0`), sin forzarla; en release la version del paquete debe coincidir con el tag. El redeploy de una version ya publicada en retain no esta permitido.

## Deteccion de stack

`detectStack` detecta el tipo de libreria desde los archivos del repositorio:

- `pom.xml`: Java Maven.
- `build.gradle` o `build.gradle.kts`: Java Gradle.
- `package.json`: NPM/Yarn.
- `package.json` con `workspaces`: NPM/Yarn monorepo.
- `pyproject.toml`, `setup.py` o `setup.cfg`: Python (`poetry` o `python -m build`).

Si `LANGUAGE` viene definido, se usa como override. Valores soportados:

- Java: `java`, `maven`, `mvn`, `gradle`, `java_mvn`, `java_maven`, `java_gradle` (tambien con guion: `java-mvn`, `java-gradle`).
  - `java_mvn` / `maven` / `mvn` fuerza Maven.
  - `java_gradle` / `gradle` fuerza Gradle.
  - `java` detecta el build tool por archivos (`pom.xml` vs `build.gradle`).
- NPM: `js`, `javascript`, `node`, `nodejs`, `npm`, `yarn`.
- Python: `python`, `py`, `poetry`, `pypi`.

Si el repositorio contiene mas de un stack (Java, NPM y/o Python) al mismo tiempo, y no se define `LANGUAGE`, la funcion aborta para evitar una decision ambigua.

## Metodos

### detectStack(Map params = [:])

Detecta el stack y setea variables de entorno para el resto de las fases.

Parametros:

- `workDir`: directorio del checkout. Default: `application`.
- `language`: override opcional. Si no se informa, usa `env.LANGUAGE`.

Variables seteadas:

- `env.LIB_LANGUAGE`: `java`, `npm` o `python`.
- `env.BUILD_TOOL`: `maven` o `gradle`, solo para Java.
- `env.NPM_LIB_MODE`: `single` o `monorepo`, solo para NPM.
- `env.PYTHON_BUILD_TOOL`: `poetry` o `build`, solo para Python.

### materialize(Map params = [:])

Materializa archivos auxiliares segun el stack detectado.

- Java: delega en `javaLibFunctions.materializeBuildFiles`.
- NPM: delega en `npmLibFunctions.materializeScripts`.
- Python: delega en `pythonLibFunctions.materializeScripts` (`setup-pip-conf.sh` y `python-lib.sh`).

Parametros:

- `workDir`: directorio del checkout. Default: `application`.

### initialize(Map params = [:])

Inicializa variables de build y repositorios Nexus segun el stack.
Tambien valida temprano que existan y sean accesibles los repositorios Nexus necesarios:

- `env.REPOSITORY_URL`: proxy/cache usado para resolver dependencias.
- `env.LIB_REPOSITORY_URL`: repositorio hosted usado para publicar.

Si alguno no existe o la credencial `env.NEXUS_CREDENTIAL_ID` no tiene acceso, el pipeline falla en `Initialize` con error controlado.

Parametros:

- `workDir`: directorio del checkout. Default: `application`.
- `dockerRegistry`: registry Docker para imagenes de build. Default: `env.DOCKERREGISTRY`.

### build(Map params = [:])

Ejecuta la fase de build.

- Java: `compile`.
- NPM: `install` y `build`.
- Python: `install` y `build`.

Parametros:

- `workDir`: directorio del checkout. Default: `application`.

### test(Map params = [:])

Ejecuta la fase de test. Se puede omitir completamente definiendo `RUN_TESTS=false` en el `services.env` del proyecto.

| `RUN_TESTS` | Comportamiento |
|---|---|
| no definido o `true` | Tests corren normalmente |
| `false` | Stage omitido con mensaje en log |

Parametros:

- `workDir`: directorio del checkout. Default: `application`.

### deploy(Map params = [:])

Publica el artefacto.

- Java: `deploy`.
- NPM: `publish`.
- Python: `publish` (`twine upload` al hosted Nexus). Antes valida que la version no exista en retain.

Parametros:

- `workDir`: directorio del checkout. Default: `application`.

## Metodos de soporte

Los usa la fachada. Tambien se pueden llamar desde el pipeline.

### abortWithMensaje(String message)

Setea `env.MENSAJE` a `Pipeline: ${message}` y aborta con `error`. Lo consumen las notificaciones.

### versionFromTag()

Quita el prefijo `release-` o `release/` de `env.TAG_NAME`.

Retorna la version del tag. Si `TAG_NAME` esta vacio, aborta.

### normalizeSnapshotVersion(String version)

Quita el sufijo `-SNAPSHOT` (case insensitive). Retorna el string recortado, o null si `version` es null.

### validateProjectVersionMatchesTag()

Enruta la validacion segun `env.LIB_LANGUAGE`: `npm`, `python` o Java (default). No retorna valor. Abortos posibles: version ausente, tag distinto al proyecto, SNAPSHOT en release Java, release en snapshot Java, `LIB_PUBLICATION_TYPE` vacio o distinto de `snapshot`/`release`.

### validateJavaProjectVersionMatchesTag()

- `release`: la version del proyecto (sin `-SNAPSHOT`) debe coincidir con el tag y no puede terminar en `-SNAPSHOT`.
- `snapshot`: la version debe terminar en `-SNAPSHOT`.

Lee `env.VERSION` y `env.LIB_PUBLICATION_TYPE`.

### validateNpmProjectVersionMatchesTag()

En `release`, la version de `package.json` debe coincidir con el tag (se ignora un `-SNAPSHOT` si estuviera). En `snapshot` no exige sufijo `-SNAPSHOT`.

### validatePythonProjectVersionMatchesTag()

En `release`, la version del paquete debe coincidir con el tag. En `snapshot` no fuerza `.devN`; solo loguea la recomendacion PEP 440.

### normalizeRepositoryName(String repository)

Recorta espacios, saca el prefijo `/repository/` y las barras finales. Vacio o null retorna null.

### resolveHostedRepositoryNames(String stack)

Arma los nombres Nexus `release`, `snapshot` y `proxy`.

| stack | Default release | Default snapshot | Default proxy |
|-------|-----------------|------------------|---------------|
| `maven` | `${APP_NAME}_maven_hosted` | `${APP_NAME}_maven_hosted_snapshot` | `${APP_NAME}_maven_group` |
| `npm` | `${APP_NAME}_npm_hosted` | `${APP_NAME}_npm_hosted_snapshot` | `${APP_NAME}_npm_group` |
| `pypi` o `python` | `${APP_NAME}_pypi_hosted` | `${APP_NAME}_pypi_hosted_snapshot` | `${APP_NAME}_pypi_group` |

Cada nombre se puede pisar con la variable de entorno del stack (`MAVEN_HOSTED_REPOSITORY`, `NPM_HOSTED_REPOSITORY`, `PYPI_HOSTED_REPOSITORY` y sus pares snapshot/proxy).

Retorna un mapa `release` / `snapshot` / `proxy`. Sin `APP_NAME`, o con un stack distinto, aborta.

### configureNexusRepositories(String stack)

Setea las URLs a partir de `resolveHostedRepositoryNames`.

Variables que escribe:

- `NEXUS_REPOSITORY_RELEASE`, `NEXUS_REPOSITORY_SNAPSHOT`
- `NEXUS_REPOSITORY_RETAIN` = `/repository/{release}`
- `NEXUS_PROXY_REPOSITORY` (respeta un path que ya empiece por `/repository/`)
- `REPOSITORY_URL` (proxy)
- `LIB_REPOSITORY_URL`: snapshot o release segun `LIB_PUBLICATION_TYPE`

`NEXUS_PROXY_HOST` con `http://` o `https://` se usa tal cual (Nexus Cloud). Sin esquema, se antepone `http://`.

Sin host, o con un tipo de publicacion distinto de `snapshot`/`release`, aborta. No retorna valor.

### normalizeLanguage(String language)

Normaliza el token (minusculas, sin comillas, guiones a `_`).

| Entrada | Retorno |
|---------|---------|
| `java`, `maven`, `mvn`, `gradle`, `java_mvn`, `java_maven`, `java_gradle` | `java` |
| `js`, `javascript`, `node`, `nodejs`, `npm`, `yarn`, `pnpm` | `npm` |
| `python`, `py`, `poetry`, `pypi` | `python` |
| vacio | `''` |
| otro | el token normalizado, sin mapear |

### javaBuildToolHint(String language)

Si el token indica el tool, retorna `maven` o `gradle`. `java` generico, o un valor que no es Java, retorna null.

### detectRepositoryFiles(String workDir)

Retorna un mapa:

- `hasPom`: existe `pom.xml`
- `hasGradle`: existe `build.gradle` o `build.gradle.kts`
- `hasPackageJson`: existe `package.json`
- `hasPython`: existe `pyproject.toml`, `setup.py` o `setup.cfg`

### restoreWorkspaceOwnership(Map params = [:])

Despues de fases Docker como root, hace `chown` del workspace al uid:gid original para que `deleteDir()` no falle.

- `dockerImage`: default `env.DOCKER_IMAGE`.
- Si la imagen esta vacia o termina en `:`, no hace nada.
- Si no puede leer el owner o el `chown` falla, loguea y no aborta.

No retorna valor.

## Variables de entorno por proyecto

Estas variables se configuran en el `services.env` de cada proyecto bajo `configs/<app>/<env>/<service>/services.env`:

| Variable | Aplica a | Descripcion |
|---|---|---|
| `LANGUAGE` | Java/NPM/Python | Override de deteccion de stack |
| `LANG_VERSION` | NPM/Python | Version de Node.js o tag de Python (`3.10`..`3.14`). Default Python: `3.12` |
| `PACKAGE_MANAGER` | NPM | `yarn`, `npm` o `pnpm` |
| `DOCKER_IMAGE` | NPM/Python | Imagen Docker completa (override) |
| `NPM_LEGACY_PEER_DEPS` | NPM | Activa `legacy-peer-deps=true` |
| `NPM_PUBLISH_DIR` | NPM | Directorio de publicacion (auto-detectado en Angular) |
| `PYTHON_BUILD_TOOL` | Python | `poetry` o `build`. Si no se define: `poetry.lock` o `[tool.poetry]` → `poetry`; resto → `build` |
| `PYTHON_IMAGE_VARIANT` | Python | `slim` → `docker-agents/python:X.Y-slim` |
| `RUN_TESTS` | Java/NPM/Python | `false` para saltar tests |
| `MAVEN_HOSTED_REPOSITORY` | Java | Override del repositorio hosted release. Default: `${APP_NAME}_MAVEN_HOSTED` |
| `MAVEN_HOSTED_SNAPSHOT_REPOSITORY` | Java | Override del repositorio hosted snapshot. Default: `${APP_NAME}_MAVEN_HOSTED_SNAPSHOT` |
| `MAVEN_PROXY_REPOSITORY` | Java | Override del repositorio proxy/group. Default: `${APP_NAME}_MAVEN_GROUP` |
| `NPM_HOSTED_REPOSITORY` | NPM | Override del repositorio hosted release. Default: `${APP_NAME}_NPM_HOSTED` |
| `NPM_HOSTED_SNAPSHOT_REPOSITORY` | NPM | Override del repositorio hosted snapshot. Default: `${APP_NAME}_NPM_HOSTED_SNAPSHOT` |
| `NPM_PROXY_REPOSITORY` | NPM | Override del repositorio proxy/group. Default: `${APP_NAME}_NPM_GROUP` |
| `PYPI_HOSTED_REPOSITORY` | Python | Override del repositorio hosted release. Default: `${APP_NAME}_pypi_hosted` |
| `PYPI_HOSTED_SNAPSHOT_REPOSITORY` | Python | Override del repositorio hosted snapshot. Default: `${APP_NAME}_pypi_hosted_snapshot` |
| `PYPI_PROXY_REPOSITORY` | Python | Override del repositorio proxy/group. Default: `${APP_NAME}_pypi_group` |
| `NEXUS_PROXY_REPOSITORY` | Java/NPM/Python | Override global del proxy/group (path `/repository/...`). Si no se define, usa el default del stack |

## Ejemplo

```groovy
stage('Checkout') {
    steps {
        script {
            gitFunctions.checkoutLibrarySourceFromEvent([
                repoUrl          : env.GIT_REPO,
                credentialsId    : env.CREDENTIAL_GIT,
                targetDir        : 'application',
                branch           : params.BRANCH,
                gitlabActionType : env.gitlabActionType,
                gitlabSourceBranch: env.gitlabSourceBranch,
                gitlabBranch     : env.gitlabBranch
            ])
            libBuildFunctions.detectStack(workDir: 'application')
            libBuildFunctions.materialize(workDir: 'application')
        }
    }
}

stage('Initialize') {
    steps {
        script {
            libBuildFunctions.initialize(workDir: 'application', dockerRegistry: env.DOCKERREGISTRY)
        }
    }
}

stage('Build') {
    steps {
        script {
            libBuildFunctions.build(workDir: 'application')
        }
    }
}

stage('Test') {
    steps {
        script {
            libBuildFunctions.test(workDir: 'application')
        }
    }
}

stage('Deploy') {
    steps {
        script {
            libBuildFunctions.deploy(workDir: 'application')
        }
    }
}
```

## Ejemplo services.env — Angular workspace

```bash
# configs/edp/dev/edp-lib-angular/services.env
LANG_VERSION=22
PACKAGE_MANAGER=npm
DOCKER_IMAGE=registry.example.com:8083/docker-agents/node-chrome:22
RUN_TESTS=false
```

## Ejemplo services.env — React Native

```bash
# configs/edp/dev/edp-lib-react-native/services.env
LANG_VERSION=22
PACKAGE_MANAGER=yarn
NPM_LEGACY_PEER_DEPS=true
```

## Ejemplo services.env — Python (pyproject / Poetry)

```bash
# configs/<app>/dev/<service>/services.env
LANGUAGE=python
LANG_VERSION=3.12
PYTHON_BUILD_TOOL=poetry
# PYTHON_IMAGE_VARIANT=slim
# DOCKER_IMAGE=registry.example.com:8083/docker-agents/python:3.12
```

En `develop` se recomienda version PEP 440 developmental (ej. `1.2.3.dev0`) en `pyproject.toml`. El tag `release-x.y.z` debe coincidir con la version del paquete. Detalle de backends, fases y validacion de redeploy: `pythonLibFunctions.md`.
