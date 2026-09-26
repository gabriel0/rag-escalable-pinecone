# AWS Step Functions (awsStepFunctions)

Actualiza la definicion de una state machine, opcionalmente resguarda el JSON en S3 y aplica tags de version.

Los comandos `aws` se ejecutan via `utilsFunctions.executeCommand`. La cuenta debe estar autenticada antes de llamar a estos metodos.

## `deployStepFunction`

Orquesta el despliegue a partir del nombre visible en la consola.

### Parametros

Mapa `params`:

- `aStepFunctionName` (String, **Obligatorio**): nombre de la state machine.
- `aDefinitionFilePath` (String, **Obligatorio**): ruta del JSON de definicion. El nombre de archivo debe ser `{repo}-{version}.json`.
- `anAwsResourceType` (String, **Obligatorio** si hay bucket): prefijo de la key en S3.
- `aBucketName` (String, opcional): bucket de resguardo. Si falta, no copia a S3.
- `anAwsRegion` (String, opcional): region. Default del resto de metodos: `us-east-1`.

### Logica

1. Resuelve el ARN con `getStepFunctionArn`.
2. Si hay `aBucketName`, copia el JSON a `{anAwsResourceType}/{repo}/{archivo}` con `awsS3Functions.copyToBucket`.
3. Actualiza la definicion con `updateStepFunctionDefinition`.
4. Aplica tags `Devops_Code_Source` (nombre de archivo) y `Devops_Code_Version` (segmento entre el ultimo `-` y `.json`).

### Respuesta

No retorna valor.

### Ejemplo

```groovy
awsStepFunctions.deployStepFunction([
    aStepFunctionName : 'mi-state-machine',
    aDefinitionFilePath: 'mi-repo-1.4.0.json',
    anAwsResourceType : 'stepfunctions',
    aBucketName       : env.ARTIFACT_BUCKET,
    anAwsRegion       : env.AWS_REGION
])
```

---

## `getStepFunctionArn`

Busca el ARN con `aws stepfunctions list-state-machines` filtrando por nombre.

### Parametros

- `aStepFunctionName` (String, **Obligatorio**).
- `anAwsRegion` (String, opcional, default `us-east-1`).

### Respuesta

String con la salida del comando (ARN en texto plano).

Ante error setea `MENSAJE` a `Pipeline: Error al obtener ARN de la Step Function` y aborta.

---

## `updateStepFunctionDefinition`

Ejecuta `aws stepfunctions update-state-machine` con `--definition file://`.

### Parametros

- `aStepFunctionArn` (String, **Obligatorio**).
- `aDefinitionFileName` (String, **Obligatorio**): path del JSON. El flag es `file://{path}`.
- `anAwsRegion` (String, opcional, default `us-east-1`).

### Respuesta

Salida del comando. Ante error: `Pipeline: Error actualizando definicion de la Step Function`.

---

## `tagStepFunction`

Aplica tags con `aws stepfunctions tag-resource`.

### Parametros

- `aStepFunctionArn` (String, **Obligatorio**).
- `aBunchOfTags` (Map, **Obligatorio**): pares clave/valor. Se serializan como `key=K,value=V`.
- `anAwsRegion` (String, opcional, default `us-east-1`).

### Respuesta

Salida del comando. Si el ARN esta vacio o el mapa de tags es nulo, no aplica tags y solo loguea. Ante error: `Pipeline: Error taggeando Step Function`.

**Tags:** `#aws`, `#stepfunctions`
