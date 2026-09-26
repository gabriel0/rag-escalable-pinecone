# Funcion de utilidades varias

Libreria de apoyo del pipeline. Carga variables de entorno, resume el resultado del build, comprime artefactos y cubre tareas de configuracion, backup y Docker.

El metodo recomendado para variables es `loadMultipleVars`. `loadVars` queda para llamadas directas a una sola fuente.

## Metodos

### `validateParams(params, requiredParams, failOnError)`

Valida que un mapa tenga las claves pedidas y que sus valores no esten vacios.

-   **Parametros:**
    -   `params` (Map): mapa a validar.
    -   `requiredParams` (List<String>): claves obligatorias.
    -   `failOnError` (boolean, opcional): si es `true` (defecto) aborta el pipeline. Si es `false`, advierte y retorna `false`.
-   **Respuesta:**
    -   `true` si todas las claves existen y tienen valor.
    -   `false` si falta alguna y `failOnError` es `false`.

---

### `resumePipeline(pipelineDescription, parametros, sonarScanner)`

Imprime un resumen del pipeline: descripcion, parametros, reporte de Trivy y resultado de Sonar.

-   **Parametros:**
    -   `pipelineDescription`: texto de cabecera del resumen.
    -   `parametros` (Map, opcional): pares clave-valor. Defecto: mapa vacio.
    -   `sonarScanner` (String, opcional): texto del resultado Sonar. Defecto: `"none"`.
-   **Comportamiento:**
    -   Si `env.trivyReportFilePath` apunta a un archivo existente, agrega su contenido. Esa ruta la genera `trivyFunctions.processResult`.
    -   Si la ruta no existe o no esta definida, deja una linea indicando que el reporte no se encontro.
-   **Respuesta:**
    -   Escribe el resumen en el log. No retorna valor.

---

### `encodeBase64(text)`

Codifica un texto UTF-8 en base64.

-   **Parametros:**
    -   `text` (String): texto a codificar. No puede ser nulo ni vacio.
-   **Respuesta:**
    -   String en base64.
    -   Lanza `IllegalArgumentException` si el texto es nulo o vacio.

---

### `loadMultipleVars(script, config)`

Orquesta la carga de variables segun `env.VARTYPE`.

-   **Parametros:**
    -   `script`: objeto `script` de Jenkins, normalmente `this`.
    -   `config` (Map, opcional):
        -   `appName`: sobreescribe `env.APP_NAME`.
        -   `serviceName`: sobreescribe `env.SERVICE_NAME`.
        -   `environment`: sobreescribe `env.ENVIRONMENT`.
        -   `capa`: sobreescribe `env.CAPA`. Capas validas: `api`, `fe`, `be`, `lib`, `db`, `mob`, `ms`, `app`. Si falta o no es valida, se usa `api`.
        -   `patronImplementacion`: sobreescribe `env.patronImplementacion`. Defecto: `build_deploy`.
        -   `credentialsId`: ID de la credencial de la API. Defecto: `api_devops_parameters`. En el pipeline unificado se pasa `JEN-TOKEN-APIDEVOPS`.
        -   `gitConfigurationRepo`: repo de configs. Defecto: `env.GIT_CONFIGURATION_REPO`.
        -   `gitConfigurationBranch`: rama de ese repo. Defecto: `env.GIT_CONFIGURATION_BRANCH` o `main`.
        -   `gitConfigurationDir`: directorio de checkout. Defecto: `env.GIT_CONFIGURATION_DIR` o `pipeline-configuration`.
        -   `credentialLib`: credencial Git del checkout. Defecto: `env.GIT_CONFIGURATION_CREDENTIAL` o `env.CREDENTIAL_LIB`.
-   **Comportamiento segun `VARTYPE`:**
    -   Vacio o `api`: consulta la API. Si responde HTTP 200, carga esas variables. Si responde HTTP 404, no cancela y carga desde archivo. Cualquier otro HTTP, o un fallo de conexion, cancela el pipeline.
    -   `file`: carga solo desde archivo, sin llamar a la API.
    -   Otro valor: cancela el pipeline. Los valores admitidos son `api` y `file`.
-   **Archivos que lee el fallback y `VARTYPE=file`:**
    -   `configs/<app>/global.env`
    -   `configs/<app>/<environment>/environment.env`
    -   `configs/<app>/<environment>/<service>/services.env`
    -   Si `GIT_CONFIGURATION_REPO` esta definido, hace checkout de ese repo y lee los `.env` desde ahi. Si no, los busca en el workspace actual.
    -   Un archivo inexistente se omite. Los que existen se aplican en ese orden, y el ultimo pisa claves repetidas.
-   **API:**
    -   URL: `${API_DEVOPS}/api/v1/variables/${appName}?servicio=${serviceName}&capa=${capa}&ambiente=${environment}&patronImplementacion=${patronImplementacion}`
    -   Requiere el alta del servicio en api-devops.
    -   La credencial se inyecta como header `Authorization`.
-   **Interpolacion:**
    -   Los valores pueden usar `${VAR_NAME}`. Se resuelve primero contra el mismo origen (API o archivo) y despues contra variables de entorno ya cargadas.
    -   Una dependencia circular deja el valor original y lo informa en el log.
    -   Un placeholder sin variable se conserva y se advierte en el log.
-   **Respuesta:**
    -   Publica cada clave como variable de entorno del pipeline.

---

### `loadVars(options)`

Carga variables desde una sola fuente, sin el fallback de `loadMultipleVars`.

-   **Parametros:**
    -   `options.sourceType` (String): `api` o `file`.
    -   Con `api`, el mapa lleva `appName`, `serviceName`, `environment`, `capa` y `patronImplementacion`. Hay que envolver la llamada en `withCredentials` para que exista `apiKeyDevops`. Un HTTP 404 cancela el pipeline.
    -   Con `file`, `options.path` lleva:
        -   `currentDir`: directorio base, normalmente `pwd()`.
        -   `level1`, `level2`, `level3`: segmentos del path. Se leen `level1/global.env`, `level1/level2/environment.env` y `level1/level2/level3/services.env` cuando los niveles correspondientes estan presentes.
-   **Respuesta:**
    -   Imprime `##### Generando variables de entorno #####` y cada `CLAVE=valor` cargada.

---

### `showPipelineInfo()`

Imprime parametros del pipeline y define `env.DEPLOY_USER` con `env.gitlabUserName` o el usuario que disparo el build.

Marcado en el codigo para decomisar. No recibe parametros.

---

### `setUpApp()`

Clona `GIT_REPO` en la rama `GIT_APP_BRANCH` con la credencial `CREDENTIAL_GIT`.

Marcado en el codigo para decomisar. Si el clone falla, guarda el mensaje en `env.MENSAJE` y no aborta.

---

### `buildDeployVars()`

Arma variables de imagen y version para ambientes `dev` y `test`.

Marcado en el codigo para decomisar. Define, entre otras, `DOCKERFILE`, `PKG_VERSION`, `DOCKER_IMAGE_TAG`, `DOCKER_IMAGE_NAME`, `DOCKER_DEPLOY_CLOUD_IMAGE`, `DOCKER_DEPLOY_ONPREM_IMAGE` y `DOCKER_DEPLOY_IMAGE`.

---

### `prepareAppForBuild(anAppLanguage)`

Copia archivos de build al workspace segun el lenguaje.

-   **Parametros:**
    -   `anAppLanguage` (String): hoy solo actua con `java`, copiando `settings.xml` y `script.sh` desde `build/${LANGUAGE}/`.
-   **Respuesta:**
    -   Ante un error marca el build como `FAILURE` y aborta.

Marcado en el codigo para decomisar.

---

### `processConf(environment, gitConfSource, gitAppSource)`

En el directorio `application`, busca la rama de configuracion y copia al overlay los archivos del entorno.

-   **Parametros:**
    -   `environment` (String): entorno (`dev`, `test`, `prod`, etc.).
    -   `gitConfSource` (String): rama donde estan las configuraciones.
    -   `gitAppSource` (String, opcional): rama de la aplicacion a la que vuelve despues de copiar. Si no se pasa, no hace checkout de vuelta.
-   **Comportamiento:**
    -   Si la rama existe, copia `<environment>/configuraciones.properties` y `<environment>/secrets.properties` a `configuration/overlays/<environment>/`.
    -   Si existe el directorio `provisioning`, lo copia a la raiz del workspace y lo devuelve a `application`.
    -   Si la rama no existe, advierte y sigue sin esos archivos.
-   **Respuesta:**
    -   Ante un error de shell aborta el pipeline.

---

### `processConfServerless(environment)`

Lee `configuration/<environment>/configuraciones.properties` y escribe `application/config.json`.

-   **Parametros:**
    -   `environment` (String): entorno del archivo de propiedades.
-   **Respuesta:**
    -   Si el archivo no existe o no tiene variables, lo informa y sigue. Un error de lectura se loguea y no aborta.

---

### `processConfOnPremSrv(environment)`

Igual que `processConfServerless`, para pipelines onprem serverless: lee `configuration/<environment>/configuraciones.properties` y escribe `application/config.json`.

-   **Parametros:**
    -   `environment` (String): entorno del archivo de propiedades.

---

### `proccessReplacementConfig(environment, configFilePath, configReplacementFilePath)`

Reemplaza en un archivo de configuracion cada clave del archivo de reemplazo, usando `sed`.

-   **Parametros:**
    -   `environment` (String): entorno, solo se usa en el log.
    -   `configFilePath` (String): archivo donde se aplican los reemplazos.
    -   `configReplacementFilePath` (String): archivo de pares clave-valor a sustituir.
-   **Respuesta:**
    -   Si el archivo de reemplazo no existe o no tiene variables validas, aborta el pipeline.

El nombre del metodo conserva la grafia `proccess`.

---

### `utilsZip(sourceDir, zipFile, excludes)`

Comprime el contenido de un directorio en un zip.

-   **Parametros:**
    -   `sourceDir` (String): directorio a comprimir. Tiene que existir.
    -   `zipFile` (String): ruta del zip de salida. Crea el directorio padre si no existe.
    -   `excludes` (String, opcional): patron de exclusion del step `zip`. Defecto: vacio.
-   **Respuesta:**
    -   Confirma la creacion del zip. Si el directorio no existe, la compresion falla o el zip no queda creado, aborta el pipeline. El zip no se archiva como artefacto de Jenkins (`archive: false`).

---

### `utilsUnzip(zipFile, targetDir)`

Extrae un zip en un directorio.

-   **Parametros:**
    -   `zipFile` (String): zip a extraer. Tiene que existir.
    -   `targetDir` (String): directorio destino. Se crea si no existe.
-   **Respuesta:**
    -   Confirma la extraccion listando el destino. Si el zip no existe, la extraccion falla o el destino queda vacio, aborta el pipeline.

---

### `waitForSeconds(seconds)`

Pausa la ejecucion.

-   **Parametros:**
    -   `seconds` (int): segundos a esperar.
-   **Respuesta:**
    -   Si `seconds` es mayor a 0, espera ese tiempo. Si es 0 o negativo, solo informa que el valor no es valido y sigue.

---

### `copyFilesWithRobocopy(destinationHost, destinationPath, backupPath, options)`

Copia `./latest` a un share de Windows con Robocopy.

-   **Parametros:**
    -   `destinationHost` (String): servidor destino.
    -   `destinationPath` (String): ruta relativa en ese servidor. El destino queda `\\host\destinationPath`.
    -   `backupPath` (String): ruta relativa del log mensual `yyyy-MM.log`.
    -   `options` (Map, opcional):
        -   `retries` (int): reintentos de Robocopy. Defecto: `2`.
        -   `move` (boolean): si es `true`, agrega `/move`. Defecto: `false`.
-   **Comportamiento:**
    -   Flags fijos: `/e /z /v /tee`, mas el log.
    -   Archiva `current_log.txt` como artefacto del build.
-   **Respuesta:**
    -   Codigo Robocopy `>= 8`: aborta.
    -   Codigo `0`: aborta, porque no copio archivos.
    -   El resto de codigos menores a 8 se consideran copia correcta.

---

### `compress7Zip(destinationHost, destinationPath, backupPath, serviceName, additionalExclusions)`

Genera un zip de backup con 7-Zip sobre un share de Windows.

-   **Parametros:**
    -   `destinationHost` (String): servidor donde esta el directorio.
    -   `destinationPath` (String): ruta relativa a comprimir.
    -   `backupPath` (String): ruta relativa donde se escribe el zip.
    -   `serviceName` (String): entra en el nombre `backup_<serviceName>_yyyy-MM-dd-HH-mm.zip`.
    -   `additionalExclusions` (List<String>, opcional): exclusiones extra en formato 7-Zip (`-x!...`).
-   **Comportamiento:**
    -   Binario: `env.ZIP_COMMAND_PATH` o `C:\Program Files\7-Zip\7z.exe`.
    -   Siempre excluye `logs\`, `temp\`, `entrada` y `salida`.

---

### `deleteOldBackups(destinationHost, backupPath, retentionPeriodMonths)`

Borra archivos del directorio de backups mas viejos que el periodo de retencion.

-   **Parametros:**
    -   `destinationHost` (String): servidor de los backups.
    -   `backupPath` (String): ruta relativa del directorio.
    -   `retentionPeriodMonths` (int, opcional): meses a conservar. Defecto: `6`.
-   **Respuesta:**
    -   Si PowerShell falla, aborta el pipeline.

---

### `executeRemotePowerShell(remoteHost, script)`

Ejecuta un bloque PowerShell en un host remoto con `Invoke-Command`.

-   **Parametros:**
    -   `remoteHost` (String): nombre del equipo.
    -   `script` (String): contenido del `ScriptBlock`.

---

### `isLabelAvailable(label)`

Indica si un label de Jenkins tiene nodos asociados.

-   **Parametros:**
    -   `label` (String): nombre del label.
-   **Respuesta:**
    -   `true` si el label existe y tiene al menos un nodo. `false` en caso contrario.

---

### `addInsecureRegistries(serverLabel, registries)`

Agrega registries inseguras a `/etc/docker/daemon.json` de un agente y reinicia Docker.

-   **Parametros:**
    -   `serverLabel` (String): label del nodo donde corre el cambio.
    -   `registries` (List<String>): registries a agregar. No pisa las que ya estan; deja la lista unica.
-   **Comportamiento:**
    -   Si `daemon.json` existe, hace backup con sufijo de fecha.
    -   Si Docker no queda `active` despues del restart, restaura el backup y vuelve a reiniciar.
-   **Respuesta:**
    -   Si Docker sigue caido despues del rollback, aborta el pipeline.

---

### `prepareBackupForCommit(aPathToFile, aDestinationPath)`

Copia un archivo a un directorio destino para poder commitearlo.

-   **Parametros:**
    -   `aPathToFile` (String): path del archivo origen.
    -   `aDestinationPath` (String): path destino. Se usa el directorio padre y se conserva el nombre del archivo origen.
-   **Respuesta:**
    -   Path del archivo copiado.
    -   Si falla, aborta el pipeline.

---

### `createDockerNetwork(config)`

Crea una red Docker bridge si todavia no existe. El gateway es la primera IP usable de la subred (ultimo octeto de la direccion de red + 1).

-   **Parametros:**
    -   `config.subnet` (String): subred CIDR, por ejemplo `10.0.0.0/28`.
    -   `config.networkName` (String): nombre de la red.
-   **Respuesta:**
    -   Si falta `subnet` o `networkName`, aborta.
    -   Si la red ya existe, no la recrea.

---

### `replaceText(config)`

Reemplaza un texto literal dentro de un archivo.

-   **Parametros:**
    -   `config.filePath` (String): archivo a modificar.
    -   `config.placeholder` (String): texto a buscar, por ejemplo `${VAR_NAME}`.
    -   `config.value` (String): texto de reemplazo.
-   **Respuesta:**
    -   Si el archivo no existe, aborta.
    -   Si el marcador no esta en el archivo, advierte y no escribe cambios.
    -   Reemplaza todas las apariciones del marcador.

---

### `updateChangelog(params)`

Crea o actualiza `changelog.md` de una imagen Docker. Las entradas nuevas van al inicio.

Formato:

```text
# dd/MM/yyyy
- Version {version}
```

-   **Parametros:**
    -   `params.dockerPath` (String, obligatorio): directorio de la imagen dentro del repositorio docker-build.
    -   `params.version` (String, obligatorio): tag publicado.
    -   `params.date` (String, opcional): fecha `dd/MM/yyyy`. Defecto: fecha actual en `America/Argentina/Buenos_Aires`.
-   **Respuesta:**
    -   Ruta relativa de `changelog.md`.
    -   Si faltan `dockerPath` o `version`, retorna `null` y no aborta.
    -   Si la version ya es la primera entrada, no modifica el archivo.

---

### `readVersionsToml(fileName)`

Lee la seccion `[versions]` de un catalogo Gradle TOML.

Ejemplo de entrada:

```toml
[versions]
activity-compose = "1.8.0"
core-ktx = "1.12.0"

[libraries]
```

-   **Parametros:**
    -   `fileName` (String, opcional): archivo a leer. Defecto: `libs.versions.toml`.
-   **Comportamiento:**
    -   Ignora comentarios (`#`) y lineas vacias.
    -   Solo toma claves de `[versions]`, hasta la siguiente seccion.
    -   Quita comillas dobles que envuelven el valor.
-   **Respuesta:**
    -   `Map<String, String>` con las versiones.
    -   Si el archivo esta vacio, no tiene `[versions]` o esa seccion no tiene propiedades, imprime el error y retorna `null`.

---

## Metodos internos

No se invocan desde el Jenkinsfile. Los usa `loadMultipleVars` y `loadVars`.

### `loadVarsApiWithFileFallback(script, config)`

Llama a la API con `failOnNotFound = false`. Si la respuesta es 404, continua con `loadVarsFile`.

### `loadVarsApi(options)`

Consulta api-devops y publica el JSON como variables de entorno. Retorna `true` si cargo variables. Retorna `false` solo cuando `failOnNotFound` es `false` y el HTTP es 404. En cualquier otro error aborta.

Requiere la variable `apiKeyDevops` en el entorno.

### `loadVarsFile(path)`

Arma las rutas `global.env`, `environment.env` y `services.env` a partir de `currentDir`, `level1`, `level2` y `level3`, y delega cada archivo existente en `loadEnvFile`.

### `loadEnvFile(filePath)`

Lee un `.env`. Ignora lineas vacias y comentarios que empiezan con `#` o `//`. Acepta `CLAVE=valor`, quita comillas simples o dobles que envuelven el valor e interpola `${VAR_NAME}`. Si el archivo no existe, lo omite.

### `resolveConfigurationBaseDir(options)`

Si hay repo de configuracion, hace checkout y retorna esa ruta. Si no, retorna el workspace actual.

### `interpolate(value, context)`

Resuelve `${VAR_NAME}` de forma recursiva. Falla con `RuntimeException` si detecta una dependencia circular.

## Ejemplos de uso

### `loadMultipleVars`

Uso recomendado. Con `VARTYPE` vacio o `api` intenta la API y, ante 404, el archivo. Con `VARTYPE=file` lee solo archivos.

```groovy
stage("Carga de variables") {
    steps {
        script {
            utilsFunctions.loadMultipleVars(this, [
                capa: "${env.CAPA}",
                credentialsId: "JEN-TOKEN-APIDEVOPS"
            ])
        }
    }
}
```

### `loadVars` contra la API

Un 404 cancela el pipeline. La credencial tiene que existir como `apiKeyDevops`.

```groovy
stage("Load Variables") {
    steps {
        withCredentials([string(credentialsId: 'JEN-TOKEN-APIDEVOPS', variable: 'apiKeyDevops')]) {
            script {
                utilsFunctions.loadVars([
                    sourceType: "api",
                    appName: env.APP_NAME,
                    serviceName: env.SERVICE_NAME,
                    environment: env.ENVIRONMENT,
                    capa: env.CAPA,
                    patronImplementacion: "deploy"
                ])
            }
        }
    }
}
```

### `loadVars` desde archivo

```groovy
stage("Load Variables") {
    steps {
        script {
            utilsFunctions.loadVars([
                sourceType: "file",
                path: [
                    currentDir: pwd(),
                    level1: "configs/${env.APP_NAME}",
                    level2: "${env.ENVIRONMENT}",
                    level3: "${env.SERVICE_NAME}"
                ]
            ])
        }
    }
}
```

Salida esperada:

```text
##### Generando variables de entorno #####
APP_NAME=trfmep
APP_SRC=src
LANGUAGE=netcore
LANG_VERSION=6.0
ABORT_ON_TRIVY=0
ABORT_TRIVY_SEV=CRITICAL
```

### Resumen, changelog y catalogo Gradle

```groovy
utilsFunctions.resumePipeline("Despliegue finalizado", [
    Servicio: env.SERVICE_NAME,
    Ambiente: env.ENVIRONMENT
], sonarScanner)

def changelog = utilsFunctions.updateChangelog([
    dockerPath: "images/${env.SERVICE_NAME}",
    version: env.CONTAINER_IMAGE_TAG
])

def versions = utilsFunctions.readVersionsToml('libs.versions.toml')
```

**Tags:** `#utils`
