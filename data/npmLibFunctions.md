# Funciones para librerias npm/yarn/pnpm

Orquesta la compilacion, pruebas y publicacion de librerias npm/yarn/pnpm en Nexus.
Los scripts shell viven en `resources/nodejs/` y se materializan en el workspace del job.

## Estrategia de publicacion

- Commits en `develop`: publican en el repositorio snapshot con `dist-tag snapshot`.
- Tags `release-*`: publican en el repositorio retain con `dist-tag latest`.
- El tag `release-x.y.z` debe crearse sobre la rama `releases` o, si esa no existe, `release/x.y.z`.
- Los releases validan que la version no exista previamente en retain para evitar redeploy.

## Metodos

**materializeScripts**

Copia scripts desde la libreria compartida al directorio de trabajo.

Parametros (`Map`):

- `targetDir` (opcional): directorio destino. Default `application`.
- `mode` (opcional): `single` (paquete unico) o `monorepo` (workspaces). Default `single`.

**initializeLibEnv**

Inicializa variables de entorno para publish (URLs Nexus, dist-tag, imagen Docker).

Parametros (`Map`):

- `workDir` (opcional): default `application`.
- `monorepo` (opcional): `true` exige workspaces en `package.json` o `packages` en `pnpm-workspace.yaml`; `false` lo prohibe.
- `dockerRegistry` (opcional): host del registry Docker. Default `env.DOCKERREGISTRY`.

Requiere `env.LIB_PUBLICATION_TYPE`, `env.APP_NAME`, `env.NEXUS_PROXY_HOST`.

**Deteccion de Angular workspace**

Si el `package.json` raiz tiene `"private": true` y existe `angular.json`, se asume un Angular workspace y se busca automaticamente:

1. El primer proyecto con `projectType: "library"` en `angular.json`.
2. Su `package.json` (ej: `projects/cromaui/angular/package.json`) como fuente de `name` y `version`.
3. El campo `dest` de `ng-package.json` del proyecto para determinar `env.NPM_PUBLISH_DIR` (ej: `dist/cromaui/angular`).

De esta forma, `env.PACKAGE_NAME`, `env.VERSION` y `env.NPM_PUBLISH_DIR` reflejan la libreria real, no el workspace root.

**Deteccion de monorepo pnpm / root private**

- `pnpm-workspace.yaml` con `packages` se trata como monorepo. Un yaml sin `packages` (ej. solo `allowBuilds`) sigue siendo paquete unico.
- Si el root es `private` y no es Angular, se resuelve el manifest publicable con `NPM_LIB_DIR` o, si hay un solo paquete no-private en el workspace, se usa ese.

**Variables de entorno configurables por proyecto (en `services.env`)**

| Variable | Descripcion | Default |
|---|---|---|
| `LANG_VERSION` | Version de Node.js para la imagen Docker | Auto-detectado (`.nvmrc`, `engines.node`) |
| `PACKAGE_MANAGER` | Package manager: `yarn`, `npm`, `pnpm` | Auto-detectado por lockfile / workspace / `packageManager` |
| `PNPM_VERSION` | Version de pnpm para corepack | Campo `packageManager` o `11.15.1` |
| `DOCKER_IMAGE` | Imagen Docker completa para el build | `node-alpine:<LANG_VERSION>` |
| `NPM_LEGACY_PEER_DEPS` | Activa `legacy-peer-deps=true` en `.npmrc` | `false` |
| `NPM_PUBLISH_DIR` | Directorio desde donde se ejecuta el publish | Auto-detectado para Angular, `.` para el resto |
| `NPM_PUBLISH_SCRIPT` | Script de `package.json` que reemplaza el publish default | (ninguno) |
| `NPM_LIB_DIR` | Directorio del paquete publicable en monorepos con root private | Auto si hay un solo publicable |
| `RUN_TESTS` | `false` para saltar la etapa de tests | `true` |

**runPhase**

Ejecuta una fase del script npm dentro de contenedor Docker.

Parametros:

- `phase`: `install`, `build`, `test` o `publish`.
- `workDir`, `mode`, `dockerImage`, `credentialsId` (opcionales).

Antes de `publish`, si `env.LIB_PUBLICATION_TYPE` es `release`, se valida que los paquetes publicables no existan ya en el repositorio retain. Si algun paquete ya existe con la misma version, el pipeline aborta con `abortWithMensaje` (notificacion controlada).

El publish se ejecuta desde `env.NPM_PUBLISH_DIR` si esta definido; en caso contrario desde el directorio de trabajo. Esto permite publicar correctamente librerias Angular cuyo artefacto vive en `dist/`.

Los `dockerArgs` montan caches de npm, yarn y pnpm en el workspace del job (`/.npm`, `/.yarn`, `/.pnpm-store`) para reutilizarlos entre fases del mismo build.

## Metodos de soporte

### detectMode(Map params = [:])

Retorna `single` o `monorepo` y lo guarda en `env.NPM_LIB_MODE`.

- `workDir`: default `application`.
- `monorepo` si `package.json` tiene `workspaces`, o si `pnpm-workspace.yaml` tiene `packages`.
- Un `pnpm-workspace.yaml` sin `packages` (por ejemplo solo `allowBuilds`) sigue en `single`.

### resolveWorkspacePatterns(String workDir, Map rootPkg)

Retorna la lista de patterns.

1. `packages` de `pnpm-workspace.yaml`, si existe y tiene `packages`.
2. `workspaces.packages` si `workspaces` es un mapa.
3. `workspaces` si es una lista.
4. Lista vacia.

### encodeNpmPackageName(String packageName)

URL-encode del nombre. `+` pasa a `%20` y `%40` vuelve a `@`, para que el scope quede como `@scope%2Fnombre`.

### collectPublishablePackages(String workDir, boolean monorepo)

Retorna una lista de mapas `name` / `version`, sin paquetes `private`.

- Paquete unico: el root, salvo que sea private. Si el root es private y `PACKAGE_NAME`/`VERSION` ya apuntan a otro manifest (Angular o `NPM_LIB_DIR`), usa esos.
- Monorepo: recorre los patterns de `resolveWorkspacePatterns` y toma cada `package.json` no private con nombre y version.

### validateNpmRedeployAllowed(String workDir, boolean monorepo)

Solo en `LIB_PUBLICATION_TYPE=release`. Baja el metadata de cada paquete publicable desde `LIB_REPOSITORY_URL`. Si el JSON contiene la version entre comillas, aborta: ya existe en retain.

Sin paquetes publicables, aborta. En snapshot no valida. Credencial: `NEXUS_CREDENTIAL_ID`. No retorna valor.

### detectNodeMajorVersion(String workDir, Map pkg)

1. `env.LANG_VERSION`.
2. Major de `.nvmrc` (sin la `v` inicial).
3. Primer numero de `engines.node`.
4. `20`.

## Deteccion de package manager

Los scripts `npm-lib.sh` y `npm-monorepo-lib.sh` detectan el package manager con el siguiente orden de prioridad:

1. Variable `PACKAGE_MANAGER` (override explicito; valores validos: `pnpm` | `yarn` | `npm`).
2. `pnpm-lock.yaml` o `pnpm-workspace.yaml` presente → `pnpm`.
3. `yarn.lock` presente → `yarn`.
4. `package-lock.json` presente → `npm`.
5. `.yarnrc.yml` o `.yarnrc` presente → `yarn`.
6. Campo `packageManager` en `package.json` (ej: `"packageManager": "pnpm@11.x"`) → el indicado.
7. Default: `npm`.

pnpm se activa con corepack contra el proxy Nexus (`COREPACK_NPM_REGISTRY`), sin salida a registry.npmjs.org.

## Tests en proyectos Angular (Karma)

Para proyectos Angular (`angular.json` presente), los scripts realizan automaticamente:

1. Exportan `CI=true` (el karma builder de Angular usa `singleRun: true` al detectarlo).
2. Detectan / instalan Chromium si no hay binario disponible.
3. Ejecutan `ng test --watch=false --browsers=ChromeHeadless` (launcher built-in de `karma-chrome-launcher`).

No se requiere `karma.conf.js` en el proyecto. Si se necesita una imagen diferente con Chrome incluido, se puede indicar en `services.env`:

```bash
DOCKER_IMAGE=registry.example.com:8083/docker-agents/node-chrome:22
```

## Scripts en resources/nodejs/

| Archivo | Uso |
|---------|-----|
| `setup-npmrc.sh` | Auth, registry Nexus, cache npm/yarn/pnpm y logs en workspace |
| `rewrite-yarn-lock.sh` | Proxy del lockfile yarn |
| `npm-lib.sh` | Paquete unico |
| `npm-monorepo-lib.sh` | Monorepo npm/yarn/pnpm workspaces |

## Pipelines consumidores

- `buildLibs.groovy`
