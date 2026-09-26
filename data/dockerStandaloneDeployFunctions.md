# Funciones de Despliegue Standalone con Docker (dockerStandaloneDeployFunctions)

Esta libreria implementa el orquestador `standalone`: despliega un contenedor Docker directamente en un nodo agente de Jenkins (sin Kubernetes/ECS) mediante `docker pull` + `docker run`, incluyendo validaciones previas del host y verificacion post-despliegue.

## `validatePrerequisites`

Valida los prerequisitos del host de despliegue standalone **antes** del build (warm-up), ejecutando las comprobaciones directamente en el agente Jenkins destino.

### Parametros

| Parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `agentLabel` | String | Si (o via `env`) | Label del agente Jenkins donde ejecutar las validaciones. Si no se indica, usa `env.DEPLOY_AGENT_LABEL` o `env.DOCKER_RUNNER_HOST`. |
| `network` | String | No | Red Docker a verificar (`docker network inspect`). Si no se indica, usa `env.DOCKER_NETWORK` o `env.DOCKER_NW`. |
| `envFile` | String | No | Ruta del archivo `--env-file` a verificar que exista en el host. Si no se indica, usa `env.DOCKER_ENV_FILE`. |
| `volumes` | String | No | Volumenes (separados por espacios, formato `host:contenedor`) a verificar que la ruta host exista. Si no se indica, usa `env.DOCKER_VOLUMES`. |
| `nexusDockerHost` | String | Si (o via `env`) | Host del registry Nexus Docker. Si no se indica, usa `env.NEXUS_DOCKER_HOST`. |
| `nexusCredId` | String | Si (o via `env`) | Credencial Jenkins para el registry Nexus. Si no se indica, usa `env.NEXUS_CREDENTIAL_ID`. |

### Logica de Ejecucion

1.  **Validacion de obligatoriedad**: Aborta con `error` si falta `agentLabel`, o si falta `nexusDockerHost` o `nexusCredId`.
2.  **Ejecucion en el nodo** (`node(agentLabel) { ... }`):
    - Verifica que el daemon Docker responda (`docker info`).
    - Si se indico `network`, verifica con `docker network inspect` que la red exista; si no, aborta con `error` indicando que debe crearse antes de desplegar.
    - Si se indico `envFile`, verifica que el archivo exista en el host (`test -f`).
    - Si se indicaron `volumes`, por cada uno extrae la ruta host (parte antes de `:`) y verifica que exista (`test -e`).
3.  Si todas las verificaciones pasan, informa que los prerequisitos fueron validados correctamente.

### Variables de Entorno Relevantes

- `env.DEPLOY_AGENT_LABEL` / `env.DOCKER_RUNNER_HOST`: Valores por defecto de `agentLabel`.
- `env.DOCKER_NETWORK` / `env.DOCKER_NW`: Valores por defecto de `network`.
- `env.DOCKER_ENV_FILE`: Valor por defecto de `envFile`.
- `env.DOCKER_VOLUMES`: Valor por defecto de `volumes`.
- `env.NEXUS_DOCKER_HOST`: Valor por defecto de `nexusDockerHost`.
- `env.NEXUS_CREDENTIAL_ID`: Valor por defecto de `nexusCredId`.
- `env.MENSAJE`: Se establece con el detalle del error antes de abortar el pipeline.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Warm-up Standalone') {
    steps {
        script {
            dockerStandaloneDeployFunctions.validatePrerequisites([
                agentLabel: env.DEPLOY_AGENT_LABEL,
                network: env.DOCKER_NETWORK,
                envFile: env.DOCKER_ENV_FILE,
                volumes: env.DOCKER_VOLUMES
            ])
        }
    }
}
```

---

## `call` (invocacion directa: `dockerStandaloneDeployFunctions(...)`)

Funcion principal (`def call(Map params)`), por lo que se invoca directamente con el nombre de la libreria. Despliega un contenedor Docker en un nodo Jenkins slave mediante `docker pull` + `docker run`.

### Parametros

| Parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `agentLabel` | String | **Si** | Label del agente Jenkins donde ejecutar Docker. |
| `image` | String | **Si** | Imagen completa **con tag** a desplegar. |
| `containerName` | String | **Si** | Nombre del contenedor Docker resultante. |
| `nexusCredId` | String | **Si** | Credencial Jenkins para login en el registry Nexus. |
| `nexusDockerHost` | String | **Si** (o inferido) | Host del registry Nexus. Si no se indica, se intenta inferir del primer segmento de `image` (via `extractRegistryHost`). |
| `publishPorts` | String | No | Mapeo de puertos para `-p` (ej. `8080:8080`). |
| `network` | String | No | Red Docker para `--network`. |
| `restart` | String | No | Politica de reinicio para `--restart`. Por defecto `unless-stopped`. |
| `volumes` | String | No | Volumenes separados por espacios para `-v` (uno o mas `host:contenedor`). |
| `envFile` | String | No | Ruta en el host para `--env-file`. |
| `runExtra` | String | No | Flags adicionales libres a agregar al `docker run`. |

### Logica de Ejecucion

1.  **Validaciones obligatorias**: Aborta con `error` si falta `agentLabel`, `image`, `containerName`, o si falta `nexusCredId` / `nexusDockerHost` (este ultimo puede resolverse automaticamente si `image` tiene formato `host/repo/...`).
2.  **Ejecucion en el nodo** (`node(agentLabel) { ... }`):
    - **Login**: `dockerBuild.dockerLogin(nexusCredId, nexusDockerHost)`.
    - **Pull**: Descarga la `image` indicada (`docker pull`).
    - **Limpieza previa**: Llama a `stopAndRemoveContainer(containerName)` para detener y eliminar cualquier contenedor previo con el mismo nombre.
    - **Armado de argumentos**: Llama a `buildDockerRunArgs(...)` para construir la cadena de flags del `docker run` (nombre, restart, puertos, red, env-file, volumenes, flags extra, imagen).
    - **Arranque**: Ejecuta `docker run -d <argumentos>`.
    - **Verificacion**: Llama a `verifyContainerRunning(containerName)` para confirmar que el contenedor haya quedado en estado `running`.
3.  Informa por consola la finalizacion exitosa del despliegue.

### Variables de Entorno Relevantes

- `env.MENSAJE`: Se establece con el detalle del error antes de abortar el pipeline (validaciones o contenedor no `running`).
- `env.NODE_NAME`: Usado solo para los mensajes informativos de log.

### Ejemplo de Uso en Jenkinsfile

```groovy
// Ejemplo real de invocacion desde deployFunctions, orquestador 'standalone'
dockerStandaloneDeployFunctions(
    agentLabel: env.DEPLOY_AGENT_LABEL?.trim() ?: env.DOCKER_RUNNER_HOST?.trim(),
    image: "${env.NEXUS_DOCKER_HOST}/${env.NEXUS_DOCKER_REPOSITORY}/${imageName}:${params.containerImageTag}",
    containerName: env.DOCKER_CONTAINER_NAME?.trim() ?: env.SERVICE_NAME?.trim(),
    nexusCredId: env.NEXUS_CREDENTIAL_ID?.trim(),
    nexusDockerHost: env.NEXUS_DOCKER_HOST?.trim(),
    publishPorts: publishPorts,
    network: env.DOCKER_NETWORK?.trim() ?: env.DOCKER_NW?.trim(),
    restart: env.DOCKER_RESTART?.trim(),
    volumes: env.DOCKER_VOLUMES?.trim(),
    envFile: env.DOCKER_ENV_FILE?.trim(),
    runExtra: env.DOCKER_RUN_EXTRA?.trim()
)
```

---

## Funciones Internas de Soporte

Estas funciones son privadas (`private`) y no se invocan directamente desde un Jenkinsfile; forman parte de la logica interna de `call`.

### `extractRegistryHost(String image)`

Infiere el host del registry a partir de una referencia de imagen completa. Toma el primer segmento antes de la primera `/` y lo devuelve solo si contiene un `.` o un `:` (indicio de que es un host, y no simplemente un nombre de repositorio); en caso contrario, o si `image` no contiene `/`, devuelve `null`.

### `stopAndRemoveContainer(String containerName)`

Detiene y elimina, si existe, un contenedor Docker con el nombre indicado:

1.  Verifica con `docker ps -a --format '{{.Names}}'` y `grep -Fxq` si ya existe un contenedor con ese nombre.
2.  Si existe, ejecuta `docker stop` y `docker rm` (ambos tolerantes a fallos, `|| true`).
3.  Si no existe, solo informa por consola que no hay contenedor previo.

### `buildDockerRunArgs(Map cfg)`

Construye la cadena de argumentos para `docker run -d` a partir de un mapa de configuracion (`image`, `containerName`, `publishPorts`, `network`, `restart`, `volumes`, `envFile`, `runExtra`):

- Siempre incluye `--name <containerName>` y `--restart <restart>`.
- Agrega condicionalmente `-p <publishPorts>`, `--network <network>`, `--env-file <envFile>`.
- Por cada volumen en `volumes` (separados por espacios), agrega un flag `-v <volumen>` independiente.
- Si hay `runExtra`, lo agrega tal cual (permite flags libres no cubiertos por los parametros anteriores).
- Finalmente agrega `image` al final de la cadena.
- Devuelve todos los argumentos concatenados con espacios.

### `verifyContainerRunning(String containerName)`

Verifica que el contenedor recien iniciado haya quedado en estado `running`:

1.  Consulta el estado con `docker inspect -f '{{.State.Status}}' <containerName>`.
2.  Si el estado no es `running`, imprime las ultimas 50 lineas de logs del contenedor (`docker logs --tail 50`, tolerante a fallos) y aborta el pipeline con `error`, dejando el detalle en `env.MENSAJE`.