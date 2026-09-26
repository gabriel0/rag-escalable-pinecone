# AWS Batch (awsBatchFunctions)

Publica una nueva revision de job definition a partir de la revision activa, un `config.json` y la imagen de contenedor. Opcionalmente resguarda el JSON en S3 y taggea el ARN.

Requiere AWS CLI autenticado, `jq` y `utilsFunctions.executeCommand`.

## `deployBatchJobDefinition`

Orquesta el alta de una revision.

### Parametros

Mapa `params`:

- `aContainerImage` (String, **Obligatorio**): imagen que queda en `containerProperties.image`.
- `aJobDefinitionName` (String, **Obligatorio**): nombre de la job definition en AWS.
- `anAwsResourceType` (String, **Obligatorio** si hay bucket): prefijo de la key S3.
- `aJobDefinitionFile` (String, **Obligatorio**): nombre del JSON de salida. Formato esperado `{repo}-{version}.json` para armar tags y la key.
- `aBucketName` (String, opcional): si esta presente, copia el JSON resultante con `awsS3Functions.copyToBucket`.
- `anAwsRegion` (String, opcional): region de los metodos que la reciben. El default interno es `us-east-1`.
- `aCustomCommand` (String, opcional): comando separado por comas. Cada token se cita como string JSON. Vacio usa `[]` (comando por defecto de la imagen).

### Logica

1. Descarga la revision `ACTIVE` a `current-job-def.json`.
2. Lee variables de entorno desde `application/config.json`.
3. Escribe `.containerProperties.command`.
4. Quita campos de runtime (`jobDefinitionArn`, `revision`, `status`, `containerOrchestrationType`), reemplaza imagen y environment, y escribe `aJobDefinitionFile`.
5. Registra la revision y obtiene el ARN.
6. Resguarda en S3 si hay bucket.
7. Taggea con `Devops_Code_Source` y `Devops_Code_Version`.

### Respuesta

No retorna valor. El ARN nuevo se imprime en el log.

### Ejemplo

```groovy
awsBatchFunctions.deployBatchJobDefinition([
    aContainerImage    : "${env.ECR_REGISTRY}/mi-job:${env.VERSION}",
    aJobDefinitionName : 'mi-batch-job',
    anAwsResourceType  : 'batch',
    aJobDefinitionFile : "mi-repo-${env.VERSION}.json",
    aBucketName        : env.ARTIFACT_BUCKET,
    anAwsRegion        : env.AWS_REGION,
    aCustomCommand     : 'python,main.py'
])
```

---

## `getBatchJobDefinition`

Describe la revision activa y la guarda en disco.

### Parametros

- `aJobDefinitionName` (String, **Obligatorio**).
- `anAwsRegion` (String, opcional, default `us-east-1`).

### Respuesta

String `current-job-def.json` (ruta del archivo escrito). Comando: `aws batch describe-job-definitions --status ACTIVE`, elemento `jobDefinitions[0]`.

Ante error: `Pipeline: Error al obtener configuracion de la job definition`.

---

## `assembleJobDefinitionEnv`

Convierte `application/config.json` (objeto clave/valor) en el array JSON de `environment` de Batch.

### Parametros

- `aJobDefinitionEnvFile` (String, **Obligatorio**): path del JSON. En el deploy se usa fijo `application/config.json`.

### Respuesta

String con objetos `{ "name": "...", "value": "..." }` unidos por coma, sin corchetes exteriores. Escapa comillas en clave y valor.

---

## `polishJobDefinitionJsonFile`

Limpia la definicion descargada y aplica imagen y environment nuevos.

### Parametros

- `aContainerImage` (String, **Obligatorio**).
- `anEnvDefinition` (String, **Obligatorio**): salida de `assembleJobDefinitionEnv`.
- `aSourceJsonFile` (String, **Obligatorio**).
- `aResultingJsonFile` (String, **Obligatorio**).

### Respuesta

Retorna `aResultingJsonFile`.

---

## `addCustomFieldInJobDefinitionJsonFile`

Asigna un campo jq sobre el JSON y reemplaza el archivo (pasa por `temp_{archivo}`).

### Parametros

- `aJsonFile` (String, **Obligatorio**).
- `aFieldToModify` (String, **Obligatorio**): path jq, por ejemplo `.containerProperties.command`.
- `aValueForAField` (String, **Obligatorio**): JSON valido para `--argjson`.

### Respuesta

No retorna valor.

---

## `registerBatchJobDefinition`

Registra la revision con `aws batch register-job-definition --cli-input-json`.

### Parametros

- `aJobDefinitionFile` (String, **Obligatorio**).
- `anAwsRegion` (String, opcional, default `us-east-1`).

### Respuesta

ARN (`--query jobDefinitionArn`). Ante error: `Pipeline: Error al registrar la configuracion de la job definition`.

---

## `tagBatchJobDefinition`

Aplica tags con `aws batch tag-resource`. El mapa se serializa como `clave=valor` separado por comas.

### Parametros

- `aJobDefinitionArn` (String, **Obligatorio**).
- `aBunchOfTags` (Map, **Obligatorio**).
- `anAwsRegion` (String, **Obligatorio** en esta firma; no tiene default).

### Respuesta

Salida del comando. ARN vacio o tags nulos: no aplica tags. Ante error: `Pipeline: Error taggeando Job Definition`.

**Tags:** `#aws`, `#batch`
