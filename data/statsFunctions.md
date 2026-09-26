# statsFunctions

Libreria para la ingesta de datos estadisticos en InfluxDB, con mecanismos de fallback a S3.

## Descripcion

Este conjunto de funciones se encarga de recolectar, formatear y enviar metricas de diversas etapas y herramientas del pipeline (Jenkins, Librerias, SonarQube, Trivy, SQL, Serverless) a una instancia de InfluxDB. Incluye un robusto mecanismo de fallback que guarda las metricas en un bucket de S3 si InfluxDB no esta disponible, y una funcion para procesar posteriormente esos datos desde S3.

---

## Funciones Principales

### `updateStatsToInfluxDB(Map params)`

Funcion orquestadora principal que determina que metricas deben ser enviadas a InfluxDB basandose en los parametros proporcionados. Llama a las funciones especificas (`updateStatJenkinsInflux`, `updateStatSonarInflux`, `updateStatTrivyInflux`, etc.) segun la disponibilidad de los datos.

#### Parametros

Un mapa `params` que puede contener las siguientes claves:

| Clave | Requerido | Descripcion |
|---|---|---|
| `influxToken` | Si | Token de autenticacion para InfluxDB. |
| `influxUrl` | Si | URL del servidor InfluxDB. |
| `influxOrg` | Si | ID de la organizacion en InfluxDB. |
| `jenkinsJob` | Si | Nombre del job de Jenkins (ej: `folder/job-name`). |
| `appName` | Si | Nombre de la aplicacion. |
| `pipeStatus` | Si | Estado final del pipeline (`SUCCESS`, `FAILED`, `ABORTED`). |
| `service` | Condicional | Nombre del servicio (requerido para Sonar y Trivy). |
| `ambiente` | Condicional | Nombre del entorno (requerido para Sonar y Trivy). |
| `trivyJsonFile` | Condicional | Ruta al archivo de reporte JSON de Trivy. Si existe, se enviaran metricas de Trivy. |
| `libPublicationType` | Condicional | Tipo de publicacion de libreria (`snapshot` / `release`). Si esta presente, se enruta a `updateStatLibraryInflux` en lugar de `updateStatJenkinsInflux`. |
| `libLanguage` | Opcional | Lenguaje detectado del pipeline de librerias (`java` / `npm`). |
| `buildTool` | Opcional | Build tool detectado para librerias Java (`maven` / `gradle`). |
| `project` | Opcional | Prefijo/proyecto de la libreria (ej. `env.PROJECT`). |
| `...` | Opcional | Otros parametros como `versionCodigo`, `buildId`, `lenguaje`, etc., son utilizados por las funciones secundarias. |

#### Logica de Ejecucion

1.  **Normalizacion de Parametros**: Limpia y asigna valores por defecto a todos los parametros recibidos.
2.  **Metricas de Jenkins/Serverless**: Si los parametros basicos del pipeline estan presentes y **no** es un pipeline de librerias (`libPublicationType` ausente), llama a `updateStatJenkinsInflux` o `updateServerlessInflux` (si `resourceType` esta definido).
3.  **Metricas de Librerias**: Si `libPublicationType` esta definido, llama a `updateStatLibraryInflux`.
4.  **Metricas de Sonar**: Si los parametros especificos de Sonar estan disponibles (a traves de variables de entorno como `overallMetricsSummary`), llama a `updateStatSonarInflux`.
5.  **Metricas de Trivy**: Si el archivo `trivyJsonFile` existe, llama a `updateStatTrivyInflux`.

#### Ejemplo de Uso

```groovy
// En el bloque post/always del pipeline
post {
    always {
        script {
            statsFunctions.updateStatsToInfluxDB([
                influxToken: env.INFLUX_TOKEN,
                influxUrl: env.INFLUX_URL,
                influxOrg: env.INFLUX_ORG,
                jenkinsJob: env.JOB_NAME,
                appName: env.APP_NAME,
                pipeStatus: currentBuild.currentResult,
                service: env.SERVICE_NAME,
                ambiente: env.ENVIRONMENT,
                versionCodigo: env.APP_VERSION,
                versionDocker: env.CONTAINER_IMAGE_TAG,
                buildId: env.BUILD_NUMBER,
                trivyJsonFile: 'reportetrivy.json',
                // ... otros parametros
            ])
        }
    }
}
```

---

### `updateStatJenkinsInflux(Map params)`

Envia las metricas de ejecucion de un pipeline de Jenkins a InfluxDB.

#### Parametros

Recibe el mismo mapa `params` que `updateStatsToInfluxDB`. Los parametros clave son `appName`, `jenkinsJob`, `pipeStatus`, `ambiente`, `servicio`, `buildId`, y `buildUser`.

#### Payload Enviado

Genera un unico punto de datos para el *measurement* `jenkins_job` con tags y fields que resumen la ejecucion del pipeline.

#### Ejemplo de Uso (Standalone)

Ideal para pipelines que solo necesitan reportar su estado de ejecucion (ej. despliegues en produccion).

```groovy
statsFunctions.updateStatJenkinsInflux([
    influxToken: env.INFLUX_TOKEN,
    influxUrl: env.INFLUX_URL,
    influxOrg: env.INFLUX_ORG,
    appName: env.APP_NAME,
    service: env.SERVICE_NAME,
    jenkinsJob: env.JOB_NAME,
    pipeStatus: currentBuild.currentResult,
    ambiente: env.ENVIRONMENT,
    buildId: env.BUILD_NUMBER,
    buildUser: env.BUILD_USER_ID
])
```

---

### `updateStatLibraryInflux(Map params)`

Envia las metricas de ejecucion de un pipeline de **librerias** (Java/NPM publicadas a Nexus) a InfluxDB, usando un bucket y un modelo de datos propios ya que el de microservicios (namespace/cluster/imagen docker) y el de SQL (motor/database) no aplican a este tipo de pipeline.

#### Bucket

`jenkins_stats_libraries` (a diferencia de `jenkins_stats` que usan los microservicios).

#### Parametros

Recibe el mismo mapa `params` que `updateStatsToInfluxDB`. Los parametros clave son `appName`, `project`, `service`, `jenkinsJob`, `pipeStatus`, `libLanguage`, `buildTool`, `libPublicationType`, `versionCodigo`, `ambiente`, `buildId`, `buildUser`, `agentName`, `pipelineDuration`, `sonarHost`, `sonarQualityGate` y opcionalmente `stageTimesJson`.

#### Payload Enviado

Genera un unico punto de datos para el *measurement* `jenkins_library_job` con tags (`aplicacion`, `proyecto`, `job_name`, `repositorio`, `branch`, `lenguaje`, `build_tool`, `tipo_publicacion`, `servicio`, `ambiente`, `status`, `agent`) y fields (`user`, `jenkins_id`, `version_codigo`, `pipeline_duration`, `sonar_host`, `sonar_status`, `sonar_status_qg`, y `stage_*` si se provee `stageTimesJson`).

#### Ejemplo de Uso (Standalone)

```groovy
statsFunctions.updateStatLibraryInflux([
    influxToken: env.API_TOKEN,
    influxUrl: env.INFLUX_URL,
    influxOrg: env.INFLUX_ORG,
    jenkinsJob: env.JOB_NAME,
    jenkinsUrl: env.JENKINS_URL,
    appName: env.APP_NAME,
    project: env.PROJECT,
    service: env.SERVICE_NAME,
    appRepoGit: env.GIT_REPO,
    appBranch: env.GIT_APP_BRANCH,
    libLanguage: env.LIB_LANGUAGE,
    buildTool: env.BUILD_TOOL,
    libPublicationType: env.LIB_PUBLICATION_TYPE,
    versionCodigo: env.VERSION,
    ambiente: env.ENVIRONMENT,
    pipeStatus: currentBuild.currentResult,
    buildUser: params.TRIGGERING_USER,
    buildId: env.BUILD_NUMBER,
    agentName: env.NODE_NAME,
    pipelineDuration: currentBuild.duration
])
```

---

### `updateStatSonarInflux(Map params)`

Envia las metricas de un analisis de SonarQube a InfluxDB.

#### Variables de Entorno Requeridas

Esta funcion depende de variables de entorno que deben ser pobladas previamente (generalmente por `sonarFunctions`):

-   `env.overallMetricsSummary`: Metricas del codigo general.
-   `env.newMetricsSummary`: Metricas del codigo nuevo.
-   `env.sonarQualityGate`: Estado del Quality Gate (`OK` o `ERROR`).

#### Payload Enviado

Genera un unico punto de datos para el *measurement* `jenkins_job`, enriqueciendo los tags con metricas de Sonar como `coverage`, `bugs`, `vulnerabilities`, etc.

---

### `updateStatTrivyInflux(Map params)`

Procesa un reporte de vulnerabilidades en formato JSON de Trivy y envia cada vulnerabilidad como un punto de datos a InfluxDB.

#### Parametros

-   `trivyJsonFile` (String, **Requerido**): Ruta al archivo JSON generado por Trivy.
-   Otros parametros como `appName`, `service`, `buildId`, `versionDocker` para etiquetar las metricas.

#### Logica de Ejecucion

1.  Verifica si el archivo `trivyJsonFile` existe.
2.  Lee y parsea el contenido del JSON.
3.  Itera sobre cada vulnerabilidad encontrada en los resultados.
4.  Para cada vulnerabilidad, crea un punto de datos en formato Line Protocol para el *measurement* `trivy_vulnerabilities`.
5.  **Manejo de Carga**: Si hay mas de 100 vulnerabilidades, las divide en *chunks* (lotes) de 100 y envia cada lote en una peticion separada para evitar sobrecargar la API de InfluxDB.
6.  Añade un timestamp en nanosegundos a **cada linea** del payload para asegurar que cada vulnerabilidad tenga la fecha correcta.
7.  Si no se encuentran vulnerabilidades, envia una unica metrica con `vulnerabilities_count=0`.

---

### `updateSqlStatsInflux(Map params)`

Envia metricas especificas para pipelines de bases de datos (SQL).

#### Parametros

Similar a `updateStatJenkinsInflux`, pero con campos adicionales relevantes para SQL como `tipo_motor` y `database`.

---

### `updateServerlessInflux(Map params)`

Envia metricas especificas para pipelines de despliegue de recursos Serverless.

#### Parametros

Similar a `updateStatJenkinsInflux`, pero con campos adicionales como `resource_type` y `resource_name`.

---

### `processS3FallbackData(Map params)`

Procesa los archivos de metricas que fueron guardados en S3 debido a fallos de conexion con InfluxDB. Esta funcion esta diseñada para ser ejecutada por un job de mantenimiento periodico.

#### Parametros

| Clave | Requerido | Descripcion |
|---|---|---|
| `influxUrl` | Si | URL del servidor InfluxDB. |
| `org` | Si | ID de la organizacion en InfluxDB. |
| `token` | Si | Token de autenticacion para InfluxDB. |
| `s3Bucket` | Si | Nombre del bucket S3 donde se guardan los fallbacks. |
| `awsCreds` | Si | ID de la credencial de AWS para acceder al bucket. |
| `s3Path` | Opcional | Ruta dentro del bucket (por defecto `influx-fallback`). |

#### Logica de Ejecucion

1.  Inicia sesion en AWS con las credenciales proporcionadas.
2.  Lista todos los archivos en la ruta de fallback de S3.
3.  Para cada archivo encontrado:
    a. Lee su contenido.
    b. Intenta enviar el contenido a InfluxDB. El *bucket* de destino en InfluxDB se extrae del nombre del archivo en S3.
    c. Si el envio es exitoso (HTTP 2xx), elimina el archivo de S3.
    d. Si el envio falla, detiene el proceso para reintentar mas tarde, asumiendo que InfluxDB sigue sin estar disponible.

---

## Funciones Auxiliares

### `sendToInfluxWithS3Fallback(Map params)`

(Funcion privada) Intenta enviar un payload a InfluxDB. Si la peticion falla con un error de servidor (HTTP 5xx) o un error de conectividad, sube el payload a un bucket de S3 para su procesamiento posterior. No activa el fallback para errores de cliente (HTTP 4xx), ya que estos indican un problema con los datos en si.

### `parseSonarOutput(sonarOutput)`

Parsea la salida de texto de un reporte de SonarQube y la convierte en un mapa de clave-valor.

### `toLineProtocol(input)`

Convierte un `Map` de Groovy o una cadena multilinea en el formato de *fields* del InfluxDB Line Protocol (ej: `key1="value1",key2=123`).

### `validateVariable(variableName, variableValue)`

Valida que una variable no sea nula o vacia.

### `transformUrl(input)` y `createURL(jenkinsUrl, jenkinsJob)`

Funciones de utilidad para construir URLs de jobs de Jenkins correctamente formateadas.

---

**Tags:** `#metricas`, `#influxdb`, `#grafana`, `#estadisticas`, `#s3`, `#fallback`, `#trivy`, `#sonar`