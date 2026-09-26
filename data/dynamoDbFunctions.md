# dynamoDbFunctions

Biblioteca de funciones para aprovisionar y operar tablas de AWS DynamoDB desde pipelines Jenkins, a partir de archivos JSON versionados.

## Descripcion

Este modulo automatiza operaciones de DynamoDB detectando en forma dinamica la tabla y el tipo de operacion segun el contenido de cada archivo JSON.  
El flujo soporta:

- `create-table`
- `batch-write-item`
- `update-item` multiple
- `delete-item` multiple

Tambien incluye validaciones de archivos JSON, soporte de `DRY_RUN` y configuracion automatica de TTL al crear tablas (si el JSON incluye tag `TTL`).

---

## Funcion Principal

### initDynamoDB

Inicializa el proceso de despliegue/operacion para DynamoDB.

#### Variables de Entorno Requeridas

| Variable | Descripcion |
|----------|-------------|
| `DIR_PREFIX_DBS` | Prefijo del directorio base donde viven los artefactos DynamoDB |
| `ENVIRONMENT` | Ambiente de despliegue (`dev`, `qa`, `pre`, `prod`, etc.) |
| `VERSION` | Version a desplegar |
| `ID_CRED_AWS` | ID de credencial AWS en Jenkins |

#### Variables de Entorno Opcionales

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `AWS_REGION` | Region AWS para ejecutar comandos de DynamoDB | `us-east-1` |
| `DRY_RUN` | Si es `true`, solo simula ejecucion sin aplicar cambios | `false` |

#### Estructura de Directorios Esperada

```text
.
└── ${DIR_PREFIX_DBS}/
    └── ${ENVIRONMENT}/
        └── ${VERSION}/
            ├── 0001-create-table.json
            ├── 0002-seed-data.json
            ├── 0003-update-items.json
            └── 0004-delete-items.json
```

#### Flujo de Ejecucion

1. Construye ruta: `./${DIR_PREFIX_DBS}/${ENVIRONMENT}/${VERSION}`
2. Valida existencia y sintaxis de archivos JSON
3. Busca todos los `.json` y los ordena alfabeticamente
4. Detecta por archivo:
   - nombre de tabla
   - tipo de operacion
5. Ejecuta comando AWS CLI correspondiente por cada archivo

---

## Deteccion Automatizada

### Deteccion de Tabla

La tabla se infiere con esta prioridad:

1. Campo `TableName` (caso `create_table`)
2. Primera clave del objeto JSON que no sea `RequestItems`
3. Primera clave dentro de `RequestItems`

### Deteccion de Operacion

El tipo de operacion se infiere por contenido:

- Si existe `TableName` -> `create_table`
- Si hay `PutRequest` o `DeleteRequest` en items -> `batch_write`
- Si item contiene `UpdateExpression` -> `update_multiple`
- Si item contiene `Key` sin `UpdateExpression` -> `delete_multiple`
- Si no se logra inferir -> `batch_write` (fallback)

---

## Formatos JSON Soportados

### 1) Crear tabla (`create_table`)

```json
{
  "TableName": "mi_tabla",
  "AttributeDefinitions": [
    { "AttributeName": "id", "AttributeType": "S" }
  ],
  "KeySchema": [
    { "AttributeName": "id", "KeyType": "HASH" }
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "Tags": [
    { "Key": "TTL", "Value": "expiresAt" }
  ]
}
```

Si el tag `TTL` existe, se ejecuta `update-time-to-live` usando ese atributo.

### 2) Escritura batch (`batch_write`)

```json
{
  "mi_tabla": [
    { "PutRequest": { "Item": { "id": { "S": "1" }, "nombre": { "S": "Ana" } } } },
    { "PutRequest": { "Item": { "id": { "S": "2" }, "nombre": { "S": "Luis" } } } }
  ]
}
```

> Limite validado por la libreria: maximo 50 items por archivo para `batch-write-item`.

### 3) Actualizacion multiple (`update_multiple`)

```json
{
  "mi_tabla": [
    {
      "Key": { "id": { "S": "1" } },
      "UpdateExpression": "SET #n = :nuevo",
      "ExpressionAttributeNames": { "#n": "nombre" },
      "ExpressionAttributeValues": { ":nuevo": { "S": "Ana Maria" } }
    }
  ]
}
```

### 4) Eliminacion multiple (`delete_multiple`)

```json
{
  "mi_tabla": [
    { "Key": { "id": { "S": "1" } } },
    { "Key": { "id": { "S": "2" } } }
  ]
}
```

---

## Ejemplo de Uso en Pipeline

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        DIR_PREFIX_DBS = 'dynamodb'
        ENVIRONMENT = 'dev'
        VERSION = '1.9.9'
        AWS_REGION = 'us-east-1'
        ID_CRED_AWS = 'aws-devops-cred'
        DRY_RUN = 'false'
    }

    stages {
        stage('Apply DynamoDB Changes') {
            steps {
                script {
                    dynamoDbFunctions.initDynamoDB()
                }
            }
        }
    }
}
```

---

## Validaciones y Seguridad

- Verifica que existan archivos JSON en el directorio objetivo.
- Valida sintaxis JSON de cada archivo antes de ejecutar AWS CLI.
- Intenta bloquear operaciones peligrosas (segun regla interna de texto).
- Usa credenciales AWS desde Jenkins (`AmazonWebServicesCredentialsBinding`).
- `DRY_RUN=true` permite revisar plan de ejecucion sin cambios reales.

---

## Manejo de Errores Comunes

### No se encontraron archivos JSON

- Verificar `DIR_PREFIX_DBS`, `ENVIRONMENT` y `VERSION`.
- Confirmar que la ruta construida contenga `.json`.

### No se pudo determinar la tabla

- Asegurar que el JSON tenga `TableName`, o formato `{ "tabla": [...] }`, o `RequestItems`.

### Exceso de items en batch write

- Dividir archivo cuando tenga mas de 50 items.

### Credenciales o permisos AWS insuficientes

- Revisar `ID_CRED_AWS`.
- Confirmar permisos IAM para:
  - `dynamodb:CreateTable`
  - `dynamodb:BatchWriteItem`
  - `dynamodb:UpdateItem`
  - `dynamodb:DeleteItem`
  - `dynamodb:DescribeTable`
  - `dynamodb:UpdateTimeToLive`

---

## Dependencias

- AWS CLI disponible en el agente Jenkins.
- Plugin Jenkins:
  - Pipeline Utility Steps (para `readJSON`, `writeJSON`)
  - AWS Credentials Binding
- Acceso de red a AWS DynamoDB.

---

**Tags:** `#dynamodb`, `#aws`, `#jenkins`, `#pipeline`, `#devops`, `#json`, `#ci-cd`
