# GCP Functions Library ☁️

El objetivo de esta libreria es proveer un grupo de funciones diseñadas para interactuar con varios servicios de Google Cloud Platform (GCP). 

Principalmente:

- La autenticacion para interactuar con GCP dentro de un contexto
- El despliegue de Cloud Functions 
- El despliegue de Cloud Runs
- El despliegue de Workflows
- La gestion de artefactos(Upload/Delete)

---

## Funciones Globales 🚀

Estas funciones son los puntos de entrada principales para interactuar con la libreria.

### `deployCloudfunction(Map params)`

Despliega una **Cloud Function** en GCP. Esta funcion orquesta todo el proceso, desde la validacion de parametros hasta la ejecucion del comando `gcloud`.

-   **Comportamiento**: Se conecta a GCP usando las credenciales de la cuenta de servicio, verifica los parametros obligatorios y ejecuta un comando `gcloud run deploy` con los valores proporcionados para desplegar la funcion.
-   **Parametros**:
    -   `cloudFunctionName` (requerido): Nombre de la Cloud Function.
    -   `codePath` (requerido): Ruta al codigo fuente de la funcion.
    -   `cloudFunctionVersion` (requerido): La version del artefacto de nexus
    -   `projectId` (requerido): ID del proyecto de GCP.
    -   `region` (requerido): Region de GCP.
    -   `serviceAccount` (requerido): ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP.
    -   `entryPoint` (requerido): El punto de entrada de la funcion (ej. el nombre de la funcion a ejecutar).
    -   `runtime` (requerido): El entorno de ejecucion (ej. `python311`).
    -   `secondgen` (requerido): Booleano para indicar si es una funcion de segunda generacion.
    -   `iniciativaID` (opcional): ID de la iniciativa.
    -   `debug` (opcional): Activa los logs de depuracion.

### `gcloudBuildAndUploadToArtifactRegistry(Map params)`

Construye una imagen de Docker y la sube a **Artifact Registry**. Esta funcion utiliza Cloud Build para el proceso de construccion y se encarga de generar la URL completa de la imagen.

-   **Comportamiento**: Se autentica en GCP, genera la URL de la imagen con la etiqueta (tag) y llama a la funcion `gcloudBuildsSubmit` para ejecutar el proceso de construccion y subida.
-   **Parametros**:
    -   `artifactName` (requerido): Nombre del artefacto.
    -   `artifactVersion` (requerido): Version del artefacto.
    -   `artifactExtension` (requerido): Extension del archivo del artefacto.
    -   `artifactRegistry` (requerido): Nombre del repositorio de Artifact Registry.
    -   `setBuildLogsBucket` (requerido): Bucket para almacenar los logs de construccion.
    -   `workerPool` (requerido): Pool de instancias donde se ejecutara el proceso (ej: projects/bm-gcp-p1-dwint/locations/us-east1/workerPools/bm-gcp-ue1-p1-dwint-cpw-01)
    -   `projectId` (requerido): ID del proyecto de GCP.
    -   `region` (requerido): Region de GCP.
    -   `serviceAccount` (requerido):  ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP.
    -   `iniciativaID` (opcional): ID de la iniciativa.
    -   `cloudbuildAccount` (opcional): Cuenta de servicio para Cloud Build (si es diferente a la predeterminada).
    -   `debug` (opcional): Echo de variables pasadas a la funcion.

### `deployCloudRun(Map params)`

Orquesta el proceso completo de despliegue de un servicio en **Cloud Run**. Esta funcion se encarga de construir la imagen, validarla y, finalmente, desplegarla.

-   **Comportamiento**: Realiza la autenticacion, construye la URL de la imagen, verifica si ya existe una imagen con el mismo tag y, si no, procede a construir y subir la imagen. Finalmente, llama a `gcloudRunDeploy` para desplegar el servicio. Tambien incluye logica para manejar el despliegue de *sidecars*.
-   **Parametros**:
    -   `cloudRunName` (requerido): Nombre del servicio Cloud Run.
    -   `cloudRunVersion` (requerido): (requerido): La version con la cual se va a tagear la imagen de la CR a desplegar.
    -   `cloudRunArtifactToDeploy` (requerido): Nombre del artefacto a desplegar.
    -   `cloudRunArtifactExtension` (requerido): Extension del artefacto. (ej zip)
    -   `setBuildLogsBucket` (requerido): Bucket donde va a guardar los logs de Cloud Build de la construccion de la imagen.
    -   `workerPool` (requerido): Pool de instancias donde se ejecutara el proceso (ej: projects/bm-gcp-p1-dwint/locations/us-east1/workerPools/bm-gcp-ue1-p1-dwint-cpw-01)
    -   `projectId` (requerido): ID del proyecto.
    -   `region` (requerido): Region de GCP.
    -   `serviceAccount` (requerido):  ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP.
    -   `sidecarArtifactToDeploy` (opcional): Nombre del artefacto del sidecar.
    -   `sidecarVersion` (opcional): Version del sidecar.
    -   `debug` (opcional): Habilita los logs de depuracion.

### `deployWorkflow(Map params)`

Despliega un **Workflow** en GCP. Esta funcion verifica primero si el workflow ya existe antes de intentar desplegar una nueva version.

-   **Comportamiento**: Se autentica en GCP, verifica si el `workflowName` ya existe en la region y proyecto especificados. Si existe, actualiza el workflow usando los archivos de definicion.
-   **Parametros**:
    -   `serviceAccount` (requerido):  ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP.
    -   `gcpProjectId` (requerido): ID del proyecto de GCP.
    -   `gcpRegion` (requerido): Region de GCP.
    -   `workflowName` (requerido): Nombre del workflow.
    -   `workflowFileName` (requerido): Nombre del archivo YAML del workflow.
    -   `workerPool` (requerido): Pool de instancias donde se ejecutara el proceso (ej: projects/bm-gcp-p1-dwint/locations/us-east1/workerPools/bm-gcp-ue1-p1-dwint-cpw-01)
    -   `workflowEnvFileName` (opcional): Nombre del archivo YAML de variables de entorno.
    -   `workflowFolderName` (opcional): Nombre de la carpeta que contiene los archivos del workflow.
    -   `debug` (opcional): Habilita los logs de depuracion.

### `scanAndUploadPythonRequirements(Map params)`

Descarga, escanea con Trivy y sube un conjunto de dependencias de Python a un registro de artefactos.

-   **Comportamiento**: Descarga las dependencias especificadas en un archivo `requirements.txt`, las escanea en busca de vulnerabilidades con Trivy. Si no se encuentran vulnerabilidades por encima del umbral definido, sube los paquetes escaneados a un registro de artefactos de GCP a traves de una Cloud Function.
-   **Parametros**:
    -   `gcpServiceAccount` (requerido):  ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP..
    -   `gcpProjectId` (requerido): ID del proyecto de GCP.
    -   `gcpRegion` (requerido): Region de GCP.
    -   `cloudFunctionUrl` (requerido): URL de la Cloud Function.
    -   `artifactRegistry` (requerido): Nombre del repositorio de Artifact Registry.
    -   `requirementsFile` (requerido): Ruta al archivo `requirements.txt`.
    -   `downloadDir` (requerido): Directorio para descargar los paquetes.
    -   `severityThreshold` (requerido): Umbral de severidad de Trivy (ej. `HIGH`, `CRITICAL`).
    -   `trivyOutputFile` (requerido): Ruta y nombre para el archivo de salida del escaneo.

---

## Funciones Privadas 🤫

Estas funciones estan diseñadas para ser llamadas internamente por las funciones globales. Aunque puedes usarlas directamente, su proposito principal es soportar la logica de las funciones principales.

### `gcpLoggedInContext(String credentialId, Closure body)`

Esta es la funcion principal de autenticacion.

-   **Comportamiento**: Inicia un contenedor de Docker con las herramientas de GCP necesarias, se autentica usando un archivo de credenciales de servicio de Jenkins y luego ejecuta el bloque de codigo (`Closure body`) proporcionado. Esto garantiza que cualquier comando de GCP dentro del bloque se ejecute con las credenciales correctas.
-   **Parametros**:
    -   `credentialId`:  ID del secreto de jenkins que posee credenciales de la cuenta con la que nos vamos a loggear a GCP.
    -   `body`: El bloque de codigo que se ejecutara despues de la autenticacion.

### `setGkeAuth(String aGcpProject, String aGkeCluster, String aGcpRegion)`

Configura las credenciales de acceso para un cluster de GKE.

-   **Comportamiento**: Establece variables de entorno para el proyecto, cluster y region, y luego ejecuta comandos `gcloud` para configurar el acceso al cluster.

### `BuildTagImageGCP(String project, String region, String artifactName, String imageName, String version = null)`

Construye la URL completa de una imagen en Artifact Registry.

-   **Comportamiento**: Combina los parametros del proyecto, region, nombre del repositorio, nombre de la imagen y version para crear una cadena de URL completa y formateada.

### `validateImageByTag(String artifactUrl, String tag)`

Verifica si una imagen con un tag especifico existe en Artifact Registry.

-   **Comportamiento**: Llama a `gcloud container images list-tags` y analiza la salida JSON para determinar si existe una entrada que coincida con el tag.

### `getImageTagsLatest(String artifactUrl)`

Obtiene los tags de la version 'latest' de una imagen.

-   **Comportamiento**: Utiliza `gcloud container images list-tags` con un filtro para obtener los tags asociados a la version `latest`.

### `gcloudBuildsSubmit(String projectId, String region, String imageUrl, String tag, ...)`

Ejecuta el proceso de construccion de Cloud Build.

-   **Comportamiento**: Crea dinamicamente un archivo YAML de configuracion para Cloud Build, que incluye los pasos para construir y subir una imagen de Docker. Luego, ejecuta el comando `gcloud builds submit` para iniciar la construccion.

### `gcloudRunDeploy(String cloudRunName, String projectId, String region, String imageUrl, ...)`

Ejecuta el comando de despliegue para Cloud Run.

-   **Comportamiento**: Construye el comando `gcloud run deploy` con todos los parametros necesarios y lo ejecuta. Tambien tiene logica para manejar el despliegue con sidecars.

### `deleteImageFromArtifactRegistry(String imageUrl, String tag, ...)`

Elimina una imagen de Docker de Artifact Registry.

-   **Comportamiento**: Ejecuta el comando `gcloud container images delete` para eliminar una imagen con un tag especifico.

### `checkWorkflowExists(String projectId, String region, String workflowName)`

Verifica la existencia de un workflow en GCP.

-   **Comportamiento**: Usa `gcloud workflows list` y analiza el resultado para ver si el nombre del workflow esta en la lista.

### `updateWorkflow(String workflowName, String projectId, String region, String workflowFileName, ...)`

Actualiza un workflow existente en GCP.

-   **Comportamiento**: Construye y ejecuta el comando `gcloud workflows deploy` con la opcion de un archivo de variables de entorno si se proporciona.

### `downloadPackages(String requirementsFile, String downloadDir)`

Descarga dependencias de Python usando `pip`.

-   **Comportamiento**: Inicia un contenedor de Docker de Python para aislar el entorno, instala `pip`, y descarga los paquetes de un `requirements.txt` a un directorio especificado.

### `scanPythonPackagesTrivy(String packageDirectory, String severityThreshold, String outputFile)`

Escanea un directorio de paquetes de Python con Trivy.

-   **Comportamiento**: Inicia un contenedor de Docker de Trivy y ejecuta un escaneo de tipo `fs` (filesystem) en el directorio de paquetes. Configura un umbral de severidad y archiva el resultado del escaneo.

### `uploadDependenciesToCloudFunction(String cloudFunctionUrl, String requirementsFile, String serviceAccount, ...)`

Sube dependencias a un registro de artefactos a traves de una Cloud Function.

-   **Comportamiento**: Obtiene un token de autenticacion de `gcloud` para invocar una Cloud Function, construye la URL con los parametros necesarios y usa `curl` para enviar el archivo `requirements.txt` como cuerpo de la solicitud a la funcion.