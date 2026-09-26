# Funciones de Generacion de Manifiestos (manifestFunctions)

Esta libreria orquesta la construccion del artefacto de despliegue (manifiesto) segun el orquestador configurado, delegando la generacion real a la libreria especifica de cada tecnologia (Kustomize, Helm, ECS Task Definition) y, opcionalmente, generando configuracion adicional especifica de APIM.

## `buildManifest`

Funcion principal (`def buildManifest(Map params = [:])`). Se invoca directamente con el nombre de la libreria: `manifestFunctions.buildManifest()`.

### Parametros

| Parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `orchestrator` | String | No | Orquestador(es) a procesar, separados por `::` (ej. `eks::apim`). Si no se indica, usa `env.DEPLOY_ORCHESTRATOR`. |
| `path` | String | No | Directorio donde se ejecuta la construccion (`dir(path)`) para los flavours `eks`, `kbs` y `ecs`. Por defecto `configuration/overlays/${ENVIRONMENT}`. |
| *(resto)* | - | - | Cualquier otra clave del `Map` se propaga sin modificar hacia `_buildManifestHelm` y `_buildApimConfig` (ver mas abajo). |

### Logica de Ejecucion

1.  **Resolucion del orquestador**: Toma `params.orchestrator` o, si no viene informado, `env.DEPLOY_ORCHESTRATOR`, y lo separa por `::` para soportar multiples flavours en una misma llamada (ej. `helm::apim`).
2.  **Mapa de flavours reconocidos**:
    - `eks` (deprecado, se mantiene por compatibilidad) y `kbs`: ejecutan `kustomizeBuild.kustomizeProcess()` dentro de `path`.
    - `ecs`: ejecuta `awsEcsFunctions.createTaskDefinitionFile()` dentro de `path`.
    - `helm`: ejecuta `_buildManifestHelm(params)`.
    - `apim`: ejecuta `_buildApimConfig(params)`.
    - Las funciones se definen como *closures* (lazy evaluation) para que no se ejecuten todas al construir el mapa, sino solo la(s) seleccionada(s).
3.  **Procesamiento por flavour**: Para cada flavour indicado en `orchestrator`:
    - Si es reconocido, lo ejecuta y guarda su resultado en `returnedMap[flavour]`.
    - Si no es reconocido, solo emite un mensaje informativo (no aborta el pipeline).
4.  **Retorno**: Un `Map` con el resultado devuelto por cada flavour procesado (clave = nombre del flavour).

### Variables de Entorno Relevantes

- `env.DEPLOY_ORCHESTRATOR`: Orquestador(es) por defecto si no se pasa `orchestrator` como parametro.
- `env.ENVIRONMENT`: Usada para construir el `path` por defecto (`configuration/overlays/${ENVIRONMENT}`).

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Construccion de Manifiestos') {
    steps {
        script {
            docker.image("${env.DOCKER_PIPELINE_RUN}/${env.DOCKER_PIPELINE_IMAGE}").inside("--entrypoint=''") {
                validateFunctions.validateConfigFiles()
                manifestFunctions.buildManifest()
            }
        }
    }
}
```

---

## `_buildManifestHelm`

```groovy
def _buildManifestHelm(Map params = [:])
```

Funcion privada invocada por `buildManifest` cuando el flavour `helm` esta presente en `DEPLOY_ORCHESTRATOR`. Genera el manifiesto de Kubernetes renderizando un chart de Helm (`helm template`) y lo escribe en la carpeta de Gitops.

### Logica de Ejecucion

1.  **Resolucion de archivos de valores**: Obtiene, con precedencia, todos los archivos `env.HELM_VALUES_FILENAME` aplicables via `getAllFilesApplicationServicePrecedence(...)` y los transforma en flags `-f <archivo>`.
2.  **Argumentos predefinidos del chart**: Llama a `helmFunctions.prepareHelmChartArgs(...)` pasando el nombre del chart y los datos de la imagen del contenedor (`ECR_REGISTRY`, `ECR_REPOSITORY`, `CONTAINER_IMAGE_NAME`, `CONTAINER_IMAGE_TAG`).
3.  **Argumentos de entorno del chart**: Obtiene las propiedades del entorno via `helmFunctions.helmProccessProperties("configuration/overlays/${ENVIRONMENT}")` y las convierte en flags `--set <prefijo>.<nombre>=<valor>`.
4.  **Composicion final**: Concatena los tres bloques de argumentos y los expone en `env.HELM_CHART_ARGS`.
5.  **Renderizado**: Llama a `helmFunctions.templateWithChart(...)` con el nombre/version/origen del chart y los argumentos compuestos, obteniendo el manifiesto YAML resultante.
6.  **Escritura**: Guarda el manifiesto en `configuration/Gitops/${env.APP_NAME}/${env.ENVIRONMENT}/${env.SERVICE_NAME}-manifiesto.yaml` (misma ruta convencional que usa el flujo de Kustomize).

### Variables de Entorno Requeridas

- `HELM_CHART_LOCATION`: Origen del chart (`gitRepo` o `nexusRepo`).
- `HELM_CHART_NAME`: Nombre del chart.
- `HELM_CHART_VERSION`: Version del chart.
- `HELM_VALUES_FILENAME`: Nombre del archivo de valores a buscar con precedencia.
- `HELM_RULES_PRECEDENCE_TYPE` (opcional): Tipo de reglas de precedencia extra (ej. `apim`).
- `HELM_CHART_ENV_PREFIX`: Prefijo usado al armar los flags `--set` de propiedades de entorno.
- `HELM_CHART_REPO_TYPE`, `HELM_CHART_REPO_URL`: Origen/URL del repositorio del chart.
- `ECR_REGISTRY`, `ECR_REPOSITORY`, `CONTAINER_IMAGE_NAME`, `CONTAINER_IMAGE_TAG`: Datos de la imagen a inyectar en el chart.
- `NEXUS_CREDENTIAL_ID`: Credencial para descargar el chart si su origen es Nexus.
- `APP_NAME`, `ENVIRONMENT`, `SERVICE_NAME`: Usadas para armar la ruta de salida del manifiesto.

---

## `_buildApimConfig`

```groovy
def _buildApimConfig(Map params = [:])
```

Funcion privada invocada por `buildManifest` cuando el flavour `apim` esta presente en `DEPLOY_ORCHESTRATOR`. Genera configuracion adicional (ConfigMaps) especifica para microservicios APIM, a partir de un repositorio Git externo de configuraciones.

### Parametros

| Parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `customConfigDir` | String | No | Carpeta local donde se clona el repositorio de configuracion. Por defecto `apim-extra-config`. |
| `customConfigRepo` | String | No | URL del repositorio Git con la configuracion extra. Por defecto `git@git.example.com:apim/apim_microservicios/microservices-config.git`. |
| `customConfigBranch` | String | No | Rama a clonar. Por defecto `develop`. |
| `customConfigCredentialId` | String | No | Credencial Git a usar. Por defecto `env.CREDENTIAL_LIB`. |
| `loadExtraConfig` | String | No | Si es `'yes'`, ejecuta el proceso completo. Por defecto `env.LOAD_EXTRA_CONFIG`. |

### Logica de Ejecucion

Si `loadExtraConfig` es `'yes'`:

1.  **Checkout**: Clona `customConfigRepo` (rama `customConfigBranch`) en `customConfigDir` usando `gitFunctions.checkoutRepo(...)`.
2.  **Script de valores base (opcional)**: Si existe `pipeline/configs/apim/base/scripts/apimConfigBaseValues.sh`, lo ejecuta.
3.  **Construccion de manifiestos de configuracion**: Define dos estructuras de ConfigMap:
    - Global (`targets`): a partir de `${customConfigDir}/global/${env.ENVIRONMENT}/targets.yaml`, con destino `pipeline/configs/apim/global_shared_configs/${env.ENVIRONMENT}/automated_global_shared_values.yaml` (base `baseGlobalManifest.yaml`).
    - De microservicio (`${env.SERVICE_NAME}-config`): a partir de `application/config/config-${env.ENVIRONMENT}.yaml`, con destino `pipeline/configs/apim/configs/${env.PROJECT ?: env.APP_NAME}/${env.ENVIRONMENT}/${env.SERVICE_NAME}/automated_services_values.yaml` (base `baseMicroserviceManifest.yaml`).
    - Por cada una, invoca `helmFunctions.buildConfigManifest(...)`.
4.  **Manejo de errores**: Si algo falla, setea `env.MENSAJE`, lo imprime y aborta el pipeline con `error`.

Si `loadExtraConfig` no es `'yes'`, la funcion no hace nada.

### Variables de Entorno Requeridas

- `CREDENTIAL_LIB`: Credencial Git por defecto para clonar el repositorio de configuracion.
- `LOAD_EXTRA_CONFIG`: Habilita (`'yes'`) o deshabilita el proceso.
- `ENVIRONMENT`, `SERVICE_NAME`, `APP_NAME`, `PROJECT` (opcional): Usadas para armar las rutas de origen/destino de los ConfigMaps.

---

## `getAllFilesApplicationServicePrecedence`

```groovy
def getAllFilesApplicationServicePrecedence(
    String fileName,
    String application,
    String environment = null,
    String service = null,
    String customPrecedence = null,
    String basePath = "configs",
    String commonsDir = "commons"
)
```

Busca, dentro de `basePath`, todas las rutas existentes de un archivo `fileName` segun las reglas de precedencia de `application`/`environment`/`service`, y devuelve las encontradas ordenadas de **menor a mayor precedencia** (util para pasarlas en orden a `helm template -f`, donde el ultimo archivo aplicado tiene prioridad).

### Parametros

- `fileName` (String, **Obligatorio**): Nombre del archivo a buscar (ej. `values.yaml`).
- `application` (String, **Obligatorio**): Nombre de la aplicacion.
- `environment` (String, opcional): Ambiente (`dev`, `test`, `prod`, etc.).
- `service` (String, opcional): Nombre del servicio.
- `customPrecedence` (String, opcional): Tipo de reglas de precedencia adicionales a aplicar (ver `_buildExtraRules`, actualmente soporta `"apim"`).
- `basePath` (String, opcional): Carpeta base donde buscar los archivos. Por defecto `configs`.
- `commonsDir` (String, opcional): Nombre de la carpeta de configuracion comun. Por defecto `commons`.

### Logica de Ejecucion

1.  Obtiene las reglas de precedencia (de mayor a menor) via `_buildPrecedenceRules(...)` y las invierte (para recorrer de menor a mayor).
2.  Dentro de `basePath`, verifica con `fileExists` cual de esas rutas relativas existe.
3.  Acumula en `results` las rutas encontradas (con `basePath` antepuesto), en orden de precedencia incremental.
4.  Captura cualquier excepcion, la reporta por consola y retorna una lista vacia en caso de error (no aborta el pipeline).

### Retorno

`List<String>` con las rutas de los archivos encontrados, de menor a mayor precedencia (ideal para aplicarlas en ese orden y que la de mayor precedencia sobrescriba a las anteriores).

---

## Funciones Internas de Precedencia

Estas funciones son privadas y solo se usan como soporte de `getAllFilesApplicationServicePrecedence`.

### `_buildPrecedenceRules(String fileName, String application, String environment, String service, String commonsFolder, String typeOfPrecedence)`

Genera la lista de rutas candidatas, ordenadas de **mayor a menor** precedencia, segun las reglas predefinidas:

| Prioridad | Ruta | Precedencia |
|---|---|---|
| 100 | `${application}/${environment}/${service}/${fileName}` | Mayor |
| 200 | `${application}/${environment}/${fileName}` | |
| 300 | `${application}/${commonsFolder}/${service}/${fileName}` | |
| 400 | `${application}/${commonsFolder}/${fileName}` | Menor |

Si se indica `typeOfPrecedence`, se combinan (y reordenan por clave numerica) con las reglas devueltas por `_buildExtraRules`.

### `_buildExtraRules(String fileName, String application, String environment, String service, String commonsFolder, String typeOfPrecedence)`

Selecciona un conjunto de reglas adicionales segun `typeOfPrecedence`. Actualmente solo soporta la clave `"apim"`, delegando en `_buildPrecedenceRulesApim`.

### `_buildPrecedenceRulesApim(String fileName, String application, String environment, String service, String commonsFolder)`

Define dos reglas extra especificas de APIM, que se intercalan con las reglas predefinidas segun su prioridad numerica:

| Prioridad | Ruta | Notas |
|---|---|---|
| 50 | `pipeline/global_shared/dev/global_shared_values.yaml` | Mayor precedencia que todas las reglas predefinidas (se aplica primero al invertir el orden). |
| 450 | `${application}/${environment}/${service}/automated_services_values.yaml` | Menor precedencia que todas las reglas predefinidas. |

> Nota: Estas dos rutas ignoran los parametros `fileName` y `commonsFolder` recibidos; son rutas fijas especificas del flujo APIM.
