# Funciones de Generacion de SBOM (syftFunctions)

Esta libreria genera el SBOM (Software Bill of Materials) de una imagen Docker utilizando [Syft](https://github.com/anchore/syft) en formato CycloneDX. Se encarga de verificar/descargar la imagen en el nodo Jenkins, ejecutar el escaneo dentro de un contenedor Docker y dejar el reporte disponible como artefacto.

## `call` (invocacion directa: `syftFunctions(...)`)

Funcion principal (`def call(Map params)`), por lo que se invoca directamente con el nombre de la libreria: `syftFunctions([...])`.

### Parametros

| Parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `syftPath` | String | Si | Directorio donde se escribe el reporte SBOM. |
| `imageName` | String | Si | Nombre/referencia de la imagen, **sin** tag (ej. `host:8083/repo/mi-servicio`). |
| `imageVersion` | String | Si | Tag de la imagen a escanear. |
| `outputFormat` | String | No | Formato de salida de Syft. Por defecto `cyclonedx-json`. |
| `outputFile` | String | No | Nombre del archivo de salida. Por defecto `SYFT_{appName}_{serviceName}_{date}.json`. |
| `appName` | String | No | Componente del nombre por defecto del archivo. Si no se indica, usa `env.APP_NAME` o `unknown`. |
| `serviceName` | String | No | Componente del nombre por defecto del archivo. Si no se indica, usa `env.SERVICE_NAME` o el ultimo segmento de `imageName`. |
| `date` | String | No | Componente de fecha del nombre por defecto. Por defecto `yyyyMMdd` (fecha actual). |
| `syftImage` | String | No | Imagen Docker del agente Syft. Por defecto `registry.example.com:8083/docker-agents/syft:pipeline-test`. |
| `forceScan` | Boolean | No | Si es `true`, ignora `env.CONTAINER_IMAGE_EXIST` y fuerza el escaneo. Por defecto `false`. |
| `ensureImageLocal` | Boolean | No | Si es `true` (default), verifica que la imagen exista en el nodo Jenkins y hace `pull` si falta. |
| `registryPull` | Map | No | Parametros explicitos para `registryFunctions.downloadImage` (`registryType`, `registry`, `repository`, `dockerName`, `dockerTag`, `nexusCredId`, `awsCredId`). Si no se indica, se infieren a partir de `imageName`. |
| `nexusCredId` | String | No | Credencial Nexus a usar si no viene dentro de `registryPull` ni en `env.NEXUS_CREDENTIAL_ID`. |
| `awsCredId` | String | No | Credencial AWS/ECR a usar si no viene dentro de `registryPull` ni en `env.SERVICE_CREDS`. |

### Logica de Ejecucion

1.  **Validacion basica**: Si falta `syftPath`, `imageName` o `imageVersion`, imprime una advertencia (no aborta la ejecucion).
2.  **Chequeo de construccion previa**: Si `forceScan` es `false` y `env.CONTAINER_IMAGE_EXIST` **no** es `"false"`, se asume que no se construyo una imagen nueva y la funcion retorna sin hacer nada (no hay nada nuevo que escanear).
3.  **Aseguramiento de imagen local** (si `ensureImageLocal` es `true`):
    - Verifica con `docker image inspect` si la imagen ya esta presente en el nodo actual.
    - Si no esta, infiere (o usa `registryPull`) el `registryType` (`NEXUS` o `ECR`), `registry`, `repository`, `dockerName` y `dockerTag`, y descarga la imagen mediante `registryFunctions.downloadImage`.
    - Valida que existan las credenciales necesarias (`nexusCredId` para Nexus, `awsCredId` para ECR) antes de intentar el `pull`.
    - Si tras el `pull` la imagen sigue sin estar disponible, aborta con `error`.
4.  **Escaneo con Syft**: Ejecuta `imageScanner(...)`, que corre un contenedor Docker de Syft montando `syftPath` y el socket de Docker, generando el SBOM en el formato indicado. Si el escaneo falla, aborta el pipeline con `error`.
5.  **Publicacion de resultado**: Calcula el tamano del archivo generado y expone dos variables de entorno:
    - `env.SYFT_OUTPUT_FILE`: nombre del archivo SBOM generado.
    - `env.syftSbomFilePath`: ruta completa (`syftPath/outputFile`) del SBOM generado.

### Variables de Entorno Relevantes

- `env.CONTAINER_IMAGE_EXIST`: Si es `"false"` (o `forceScan: true`), se ejecuta el escaneo; en cualquier otro caso se omite.
- `env.APP_NAME` / `env.SERVICE_NAME`: Usadas como valores por defecto para `appName` / `serviceName` si no se pasan como parametro.
- `env.NEXUS_CREDENTIAL_ID`: Credencial Nexus por defecto para el `pull` de la imagen.
- `env.SERVICE_CREDS`: Credencial AWS por defecto para el `pull` desde ECR.
- `env.NODE_NAME`: Usada solo para el mensaje informativo de log.
- `env.SYFT_OUTPUT_FILE` / `env.syftSbomFilePath`: Establecidas por la funcion al finalizar, para ser usadas por etapas posteriores (ej. `archiveArtifacts`).

### Ejemplo de Uso en Jenkinsfile

```groovy
dir('sbom') {
    syftFunctions([
        syftPath: pwd(),
        imageName: imageName,
        imageVersion: imageVersion,
        appName: params.APP_NAME?.trim(),
        serviceName: params.SERVICE_NAME?.trim(),
        syftImage: 'registry.example.com:8083/docker-agents/syft:v1.44.0',
        forceScan: true,
        ensureImageLocal: true,
        nexusCredId: params.NEXUS_CREDENTIAL_ID?.trim()
    ])
}

post {
    always {
        script {
            def artifactPath = env.SYFT_OUTPUT_FILE?.trim() ? "sbom/${env.SYFT_OUTPUT_FILE}" : null
            if (artifactPath && fileExists(artifactPath)) {
                archiveArtifacts artifacts: artifactPath, fingerprint: true, onlyIfSuccessful: false
            }
        }
    }
}
```

---

## Funciones Internas de Soporte

Estas funciones son privadas (`private`) y no se invocan directamente desde un Jenkinsfile; forman parte de la logica interna de `call`.

### `resolveOutputFileName(Map params, String imageName)`

Resuelve el nombre del archivo de salida del SBOM.

- Si `params.outputFile` viene informado, se usa tal cual (recortando espacios).
- En caso contrario, construye el nombre con el patron `SYFT_{appName}_{serviceName}_{date}.json`, donde:
    - `appName` proviene de `params.appName` o `env.APP_NAME` (sanitizado); si no hay valor, usa `unknown`.
    - `serviceName` proviene de `params.serviceName` o `env.SERVICE_NAME` (sanitizado); si no hay valor, se infiere del ultimo segmento de `imageName`.
    - `date` proviene de `params.date` o la fecha actual (`yyyyMMdd`).

### `sanitizeFileToken(String value)`

Normaliza un texto para que sea seguro como parte de un nombre de archivo: lo pasa a minusculas y reemplaza cualquier caracter que no sea `a-z`, `0-9`, `.`, `_` o `-` por `_`.

### `ensureImagePresent(Map params, String imageName, String imageVersion)`

Garantiza que `imageName:imageVersion` este disponible en el daemon Docker del nodo actual:

1. Verifica con `isImageLocal`.
2. Si no esta presente, arma los parametros de `pull` (`registryPull` explicito o inferidos via `parseImageReference`), completa credenciales desde `params`/`env`, valida su presencia segun `registryType`, y descarga la imagen con `registryFunctions.downloadImage`.
3. Vuelve a verificar la presencia local; si sigue sin estar, aborta con `error`.

### `isImageLocal(String fullImage)`

Devuelve `true` si `docker image inspect '<fullImage>'` se ejecuta con exito (codigo de salida `0`), es decir, si la imagen ya existe en el nodo.

### `parseImageReference(String imageName, String imageVersion)`

Infiere los datos de registry a partir de `imageName` (formato `host[:puerto]/repositorio[/...]/nombre-imagen`):

- `registry`: primer segmento (host).
- `dockerName`: ultimo segmento.
- `repository`: segmentos intermedios (vacio si solo hay `host/nombre-imagen`).
- `registryType`: `ECR` si el host contiene `.dkr.ecr.` o `amazonaws.com`; en caso contrario `NEXUS`.
- `dockerTag`: el valor de `imageVersion` recibido.

Devuelve `null` si `imageName` no tiene al menos dos segmentos separados por `/` (no se puede inferir un registry valido).

---

## `imageScanner`

```groovy
def imageScanner(String imageName, String imageVersion, String syftPath, String outputFormat = "cyclonedx-json", String outputFile = "SYFT_unknown_unknown_unknown.json", String syftImage = "registry.example.com:8083/docker-agents/syft:pipeline-test")
```

Ejecuta Syft dentro de un contenedor Docker para escanear `imageName:imageVersion` y generar el SBOM en `syftPath`.

### Logica de Ejecucion

1.  Corre `docker run` (con `--network=host -u 0 --rm`), montando `syftPath` como `/usr/source` y el socket de Docker (`/var/run/docker.sock`), usando la imagen `syftImage`.
2.  Escribe el resultado en `/usr/source/{outputFile}` con el formato indicado (`-o {outputFormat}=...`).
3.  Verifica que el archivo generado exista en `syftPath/outputFile`.
4.  Revisa (heuristicamente) que el contenido incluya `bomFormat` o `components`; si no, solo emite una advertencia (no falla).
5.  Captura cualquier excepcion durante la ejecucion del `sh`.

### Retorno

- `null` si el escaneo se ejecuto correctamente.
- Un `String` con el mensaje de error/advertencia si el archivo no se genero o si ocurrio una excepcion (usado por `call` para abortar el pipeline con `error`).

---

## `callJobFunction`

```groovy
def callJobFunction(String jobName, boolean jobWait = false, boolean jobPropagate = false, Map params = [:])
```

Dispara un job de Jenkins (subjob) de forma asincrona, tipicamente para delegar la generacion del SBOM a un pipeline dedicado (ej. `syft_sbom`) en lugar de ejecutarlo inline.

### Parametros

- `jobName` (String, **Obligatorio**): Nombre del job de Jenkins a invocar.
- `jobWait` (Boolean, opcional): Si `true`, espera a que el subjob finalice. Por defecto `false`.
- `jobPropagate` (Boolean, opcional): Si `true`, propaga el resultado (falla) del subjob al pipeline actual. Por defecto `false`.
- `params` (Map, opcional): Parametros a pasar al job, convertidos automaticamente a parametros de tipo `string`.

### Logica de Ejecucion

Construye la lista de parametros del build y llama a `build job: jobName, parameters: ..., wait: jobWait, propagate: jobPropagate`. Si ocurre cualquier excepcion (ej. el job no existe), la captura, imprime una advertencia y **permite que el pipeline continue** sin esperar el escaneo SBOM (no aborta el build).

### Ejemplo de Uso en Jenkinsfile

```groovy
syftFunctions.callJobFunction(
    'syft_sbom',
    false,
    false,
    syftFunctions.syftJobParams([
        imageName: imageName,
        imageTag: imageVersion,
        appName: env.APP_NAME,
        serviceName: env.SERVICE_NAME,
        nexusCredId: env.NEXUS_CREDENTIAL_ID
    ])
)
```

---

## `syftJobParams`

```groovy
def syftJobParams(Map params = [:])
```

Funcion de ayuda que arma el `Map` de parametros esperado por el job `syft_sbom` (ver `pipes/syft_sbom/jenkinsfile.groovy`), a partir de un mapa de entrada mas simple.

### Parametros de Entrada

- `imageName` (String, opcional): Nombre de la imagen sin tag.
- `imageTag` (String, opcional): Tag de la imagen. Por defecto `latest`.
- `imageFull` (String, opcional): Referencia completa `imagen:tag`. Si no se indica, se construye a partir de `imageName` e `imageTag`.
- `appName` (String, opcional): Nombre de aplicacion.
- `serviceName` (String, opcional): Nombre de servicio.
- `nexusCredId` (String, opcional): Credencial Nexus a usar en el job destino.

### Retorno

Un `Map` con las claves esperadas como parametros del job Jenkins: `IMAGE_NAME`, `IMAGE_TAG`, `IMAGE_FULL`, `APP_NAME`, `SERVICE_NAME`, `NEXUS_CREDENTIAL_ID`.
