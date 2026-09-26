# Funciones para Gestion y Migracion de Parametros en AWS SSM Parameter Store

Esta libreria (`awsSsmMigrationFunctions.groovy`) proporciona un conjunto de funciones para interactuar con AWS Systems Manager (SSM) Parameter Store. Su objetivo principal es facilitar la recoleccion, el resumen, la migracion controlada de parametros y la configuracion masiva de parametros a partir de archivos JSON.

## Metodos Principales

### `collectParametersByTags(Map args)`

Recolecta parametros de AWS SSM Parameter Store en una cuenta y region especificas, filtrando por tags.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `credId` | String | Si | El ID de la credencial de Jenkins para autenticarse en AWS. | - |
| `region` | String | No | La region de AWS donde se buscaran los parametros. | `us-east-1` |
| `tagFiltersJson` | String | Si | Una cadena JSON que define los filtros de tags para la busqueda de parametros (ej. `'[{"Key":"Environment","Values":["dev"]}]'`). | - |

#### Retorno

Un mapa que contiene dos entradas:
- `text` (Map<String, String>): Un mapa de nombres de parametros (`String`, `StringList`) a sus valores en texto plano.
- `binary` (Map<String, String>): Un mapa de nombres de parametros (`SecureString`) a sus valores en texto plano (desencriptados).

---

### `printSummary(Map args)`

Imprime un resumen de los parametros recolectados, mostrando la cantidad y los nombres de los parametros de tipo `String` y `SecureString`.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `parametersText` | Map | No | Mapa de parametros de texto (`String`, `StringList`) a resumir. | `[:]` |
| `parametersBinary` | Map | No | Mapa de parametros seguros (`SecureString`) a resumir. | `[:]` |

---

### `pushParametersWithTags(Map args)`

Publica o actualiza parametros en AWS SSM Parameter Store en una region de destino. Incluye logica de confirmacion manual (`input`) en caso de detectar diferencias de valor o cambios de tipo.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `credId` | String | Si | El ID de la credencial de Jenkins para autenticarse en la cuenta AWS de destino. | - |
| `region` | String | Si | La region de AWS donde se publicaran/actualizaran los parametros. | - |
| `parametersText` | Map | No | Mapa de nombres de parametros a sus valores (`String`, `StringList`) para crear/actualizar. | `[:]` |
| `parametersBinary` | Map | No | Mapa de nombres de parametros a sus valores (`SecureString`) para crear/actualizar. | `[:]` |
| `destinoTagsNoBrackets` | String | No | Una cadena JSON que define los tags a aplicar a los parametros en destino, excluyendo los corchetes exteriores (ej. `{"Key":"estado","Value":"migrado"}`). | `{"Key":"estado","Value":"migrado"}` |
| `dryRun` | Boolean | No | Si es `true`, simula las operaciones sin realizar cambios reales en AWS SSM Parameter Store. | `false` |

---

### `congfigureSSMParameterStoreFromJson(String filePath, boolean dryRun = true)`

Configura o actualiza masivamente parametros en AWS SSM Parameter Store a partir de un archivo JSON.

#### Descripcion

Esta funcion lee un archivo JSON con una lista de definiciones de parametros y procede a crear o actualizar estos parametros en AWS SSM Parameter Store. Soporta parametros de tipo `String` y `StringList`. Proporciona un modo de ejecucion en seco (`dryRun`) para simular los cambios antes de aplicarlos.

#### Parametros

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `filePath` | String | Si | La ruta al archivo JSON que contiene la definicion de los parametros. | - |
| `dryRun` | Boolean | No | Si es `true`, la funcion simula las operaciones (creacion/actualizacion) sin realizar cambios reales. Los cambios propuestos se mostraran en la consola y se exportaran a un archivo de diferencias. | `true` |

#### Formato del Archivo JSON de Entrada

El archivo JSON debe ser un array de objetos, donde cada objeto representa un parametro con los siguientes campos:

| Campo | Tipo | Requerido | Descripcion | Valores Permitidos para `type` |
|---|---|---|---|---|
| `name` | String | Si | El nombre completo del parametro en AWS SSM Parameter Store (incluyendo su path, ej. `/mi-app/dev/db-host`). | - |
| `value` | String | Si | El valor del parametro. Para `StringList`, los valores deben estar separados por comas. | - |
| `type` | String | Si | El tipo de parametro. | `String`, `StringList` |

**Ejemplo de `ssm.parameterstore.json`:**

```json
[
  {
    "name": "/mi-aplicacion/dev/db-host",
    "value": "db.dev.example.com",
    "type": "String"
  },
  {
    "name": "/mi-aplicacion/dev/enabled-features",
    "value": "feature-a,feature-b,feature-c",
    "type": "StringList"
  },
  {
    "name": "/config/global/timeout",
    "value": "30000",
    "type": "String"
  }
]
```

#### Comportamiento

1.  **Lectura y Validacion**: Lee el archivo JSON y valida la estructura de cada entrada (presencia de `name`, `value`, `type`).
2.  **Verificacion de Existencia**: Para cada parametro, intenta obtener su valor actual de AWS SSM Parameter Store.
3.  **Determinacion de Accion**:
    *   **`CREATE`**: Si el parametro no existe, se creara.
    *   **`UPDATE`**: Si el parametro existe pero su valor es diferente al del archivo JSON, se actualizara.
    *   **`NO_CHANGE`**: Si el parametro existe y su valor es identico, no se realiza ninguna accion.
4.  **Modo Dry Run**: Si `dryRun` es `true`, la funcion solo imprime los iconos y mensajes de las acciones que **tomaria**, pero no ejecuta ningun comando `aws ssm put-parameter`.
5.  **Ejecucion de Cambios**: Si `dryRun` es `false`, la funcion ejecuta el comando `aws ssm put-parameter --overwrite` para crear o actualizar el parametro.
6.  **Reporte de Diferencias**: Al finalizar, genera un archivo de diferencias en el workspace (ej. `ssm.parameterstore-diff.json`), que detalla todos los parametros procesados, la accion determinada (`CREATE`, `UPDATE`, `NO_CHANGE`), el valor antiguo y el valor nuevo.
7.  **Feedback Visual**: Utiliza una serie de iconos Unicode para indicar el progreso y el resultado de cada operacion en la consola de Jenkins.

#### Uso en un Pipeline

```groovy
stage('AWS SSM Parameter Store - Sincronizar desde JSON') {
    steps {
        script {
            // Asumiendo que 'configuration/dev/ssm.parameterstore.json' es la ruta al archivo JSON
            // y que 'SERVICE_CREDS' son tus credenciales de AWS y 'AWS_REGION' la region de destino.
            awsAuthFunctions.login(SERVICE_CREDS, AWS_REGION) {
                awsSsmMigrationFunctions.congfigureSSMParameterStoreFromJson(
                    "configuration/${env.ENVIRONMENT}/ssm.parameterstore.json",
                    env.DRY_RUN == 'true' // Usar una variable de entorno para controlar el dryRun
                )
            }
        }
    }
    post {
        always {
            // Archivar el reporte de diferencias para revision
            archiveArtifacts artifacts: '**/*-diff.json', allowEmptyArchive: true
        }
    }
}
```

**Tags:** `#aws`, `#ssm`, `#parameterstore`, `#migration`, `#automation`, `#pipeline`, `#json`

