# Funciones de AWS Lambda

Esta libreria proporciona un conjunto de funciones para desplegar y gestionar funciones y capas (Layers) de AWS Lambda, facilitando la automatizacion de su ciclo de vida desde los pipelines de Jenkins.

## Uso de endpoints (manual o automatico)

Esta libreria se integra con `vars/awsEndpointUtils.groovy` para resolver e inyectar `--endpoint-url` en comandos `aws lambda`.

| Variable de entorno    | Descripcion                                            |
|------------------------|--------------------------------------------------------|
| `AWS_LAMBDA_ENDPOINT`  | URL del VPC endpoint o endpoint custom para Lambda     |

- Opcion 1 (manual): definir `AWS_LAMBDA_ENDPOINT`.
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true`, que detecta `com.amazonaws.<region>.lambda`.
- Si `AWS_LAMBDA_ENDPOINT` no esta definido, se utiliza el endpoint publico de AWS.

Ejemplo:

```groovy
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: override manual
// env.AWS_LAMBDA_ENDPOINT = "https://vpce-xxxx.lambda.us-east-1.vpce.amazonaws.com"
```

---

## `deployLambda`

Orquesta el proceso completo de despliegue para una funcion Lambda. Esta funcion se encarga de subir el artefacto de codigo a S3, actualizar el codigo y la configuracion de la Lambda, aplicar etiquetas de version y, finalmente, realizar un backup de la configuracion de la funcion.

### Parametros

- `lambdaName` (String, **Obligatorio**): El nombre de la funcion Lambda en AWS que se va a desplegar.
- `objectType` (String, **Obligatorio**): El tipo de objeto, usado para construir la ruta del backup (ej. "lambda").
- `appName` (String, **Obligatorio**): El nombre de la aplicacion, usado para la ruta del backup.
- `bucketName` (String, **Obligatorio**): El nombre del bucket de S3 donde se encuentra el artefacto de codigo (`.zip`).
- `enviroment` (String, **Obligatorio**): El entorno de despliegue (ej. "develop", "prod"), usado para la ruta del backup.
- `artifactName` (String, **Obligatorio**): El nombre del archivo del artefacto (ej. `mi-funcion-1.2.3.zip`).
- `version` (String, **Obligatorio**): La version del codigo que se esta desplegando. Se usara para etiquetar la Lambda.
- `region` (String, **Obligatorio**): La region de AWS donde se encuentra la funcion Lambda.

### Logica de Ejecucion

1.  Copia el `artifactName` desde el workspace a una ruta especifica (`lambda/<nombre-repo>/<nombre-artefacto>`) dentro del `bucketName` de S3.
2.  Llama a la funcion interna `updateCodeAndConfiguration` para actualizar el codigo de la Lambda y, opcionalmente, sus variables de entorno.
3.  Llama a `tagLambda` para aplicar los tags `codeSource` y `codeVersion` a la funcion.
4.  Llama a `backupLambda` para guardar la configuracion actual de la Lambda en un archivo JSON.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Deploy Lambda') {
    steps {
        script {
            // Se asume que las credenciales de AWS ya estan configuradas
            // y el artefacto (ej. mi-funcion-1.2.3.zip) esta en el workspace.
            awsLambdaFunctions.deployLambda(
                lambdaName: 'mi-funcion-lambda',
                objectType: 'lambda',
                appName: 'mi-aplicacion',
                bucketName: 'mi-bucket-de-artefactos',
                enviroment: 'develop',
                artifactName: 'mi-funcion-1.2.3.zip',
                version: '1.2.3',
                region: 'us-east-1'
            )
        }
    }
}
```

---

## `updateCodeAndConfiguration`

Actualiza el codigo de una funcion Lambda desde un objeto `.zip` en S3. Si existe un archivo `config.json` en el workspace, tambien actualiza las variables de entorno de la Lambda con su contenido.

### Parametros

- `lambdaName` (String, **Obligatorio**): Nombre de la funcion Lambda.
- `bucketName` (String, **Obligatorio**): Bucket S3 que contiene el codigo.
- `destinationKey` (String, **Obligatorio**): Ruta (key) completa del objeto `.zip` en S3.
- `region` (String, **Obligatorio**): Region de AWS.

### Requisitos Previos

- Para actualizar las variables de entorno, debe existir un archivo llamado `config.json` en el directorio de trabajo. Su contenido debe ser un JSON de clave-valor.

  **Ejemplo de `config.json`:**
  ```json
  {
    "DB_HOST": "database.example.com",
    "API_TIMEOUT": "30"
  }
  ```

---

## `tagLambda`

Aplica etiquetas (`tags`) a una funcion Lambda para identificar la version del codigo y su origen.

### Parametros

- `lambdaName` (String, **Obligatorio**): Nombre de la funcion Lambda.
- `artifactName` (String, **Obligatorio**): Nombre del artefacto de codigo fuente.
- `version` (String, **Obligatorio**): Version del codigo.
- `region` (String, **Obligatorio**): Region de AWS.

### Salida

- Añade los tags `codeSource` y `codeVersion` a la funcion Lambda especificada.

---

## `publishLayerVersion`

Publica una nueva version de una AWS Lambda Layer a partir de un archivo `.zip` almacenado en S3.

### Parametros

- `params` (Map, **Obligatorio**): Un mapa de configuracion con las siguientes claves:
  - `aLayerName` (String, **Obligatorio**): El nombre de la Layer.
  - `aBucketName` (String, **Obligatorio**): El bucket S3 donde se encuentra el `.zip` de la Layer.
  - `aBucketDestinationKey` (String, **Obligatorio**): La ruta (key) del archivo `.zip` en S3.
  - `anAwsRegion` (String, **Obligatorio**): La region de AWS.

### Variables de Entorno (Opcionales)

- `LMB_COMP_RUNTIME`: Runtimes compatibles (ej. `python3.9 nodejs14.x`).
- `LMB_COMP_ARCH`: Arquitecturas compatibles (ej. `x86_64 arm64`).

### Salida

- Devuelve el ARN de la nueva version de la Layer publicada.

---

## `bulkUpdateLambdasLayerAssociation`

Busca todas las funciones Lambda en una region y actualiza aquellas que usan una version antigua de una Layer especifica a la nueva version proporcionada.

### Parametros

- `params` (Map, **Obligatorio**): Un mapa de configuracion con las siguientes claves:
  - `aLayerArn` (String, **Obligatorio**): El ARN de la **nueva** version de la Layer que se debe aplicar.
  - `anAwsRegion` (String, **Obligatorio**): La region de AWS donde se buscaran las Lambdas.

### Logica de Ejecucion

1.  Obtiene una lista de todas las funciones Lambda en la region.
2.  Para cada funcion, verifica si esta usando la misma Layer (pero una version anterior).
3.  Si es asi, actualiza la configuracion de la Lambda para que apunte al nuevo ARN de la Layer.

---

## `backupLambda`

Obtiene la configuracion completa de una funcion Lambda y la guarda en un archivo JSON local, preparandola para ser versionada en un repositorio Git.

### Parametros

- `lambdaName` (String, **Obligatorio**): Nombre de la funcion Lambda.
- `objectType` (String, **Obligatorio**): Tipo de objeto (usado para la ruta, ej. 'lambda').
- `appName` (String, **Obligatorio**): Nombre de la aplicacion (usado para la ruta).
- `enviroment` (String, **Obligatorio**): Entorno del despliegue (usado para la ruta).

### Salida

- Crea un archivo JSON en la ruta `{appName}/{objectType}/{enviroment}/{lambdaName}/{lambdaName}-config.json`.