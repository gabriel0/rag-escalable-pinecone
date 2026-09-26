# Funciones para Gestion y Migracion de Secretos en AWS Secrets Manager

Esta libreria (`awsSecretsMigrationFunctions.groovy`) proporciona un conjunto de funciones para interactuar con AWS Secrets Manager. Su objetivo principal es facilitar la recoleccion, el resumen, la migracion controlada de secretos y la configuracion masiva de secretos a partir de archivos JSON.

## Metodos Principales

### `validarParametros(params)`

Realiza validaciones sobre los parametros de entrada, incluyendo la nomenclatura de cuentas AWS y el flujo de migracion ascendente entre entornos.

#### Parametros (`params` - Mapa)

| Parametro | Tipo | Requerido | Descripcion |
|---|---|---|---|
| `CUENTA_ORIGEN` | String | Si | Nombre de la cuenta AWS de origen. |
| `REGION_ORIGEN` | String | Si | Region AWS de origen. |
| `CUENTA_DESTINO` | String | Si | Nombre de la cuenta AWS de destino. |
| `REGION_DESTINO` | String | Si | Region AWS de destino. |
| `TAG_ESTADO_ORIGEN` | String | Si | Tag de estado para filtrar secretos en origen. |
| `TAGS_DESTINO` | String | Si | Tags a aplicar en los secretos de destino. |

#### Comportamiento

1.  **Validacion de Campos Obligatorios**: Verifica que todos los parametros requeridos esten presentes.
2.  **Cuentas Diferentes**: Asegura que la cuenta de origen y destino no sean la misma.
3.  **Nomenclatura de Cuentas**: Valida que los nombres de las cuentas sigan un patron especifico (`/^([A-Z0-9\-]+)-AWS-AWS-([A-Z]+)/`).
4.  **ID Interno Consistente**: Si la nomenclatura es correcta, verifica que el ID interno de las cuentas de origen y destino coincida.
5.  **Flujo Ascendente**: Valida que la migracion sea ascendente en el orden de entornos predefinido (`DEV`, `TEST`, `PRE`, `PREPRO`, `PROD`) y sin saltar etapas.
6.  **Advertencia Fuera de Norma**: Si las cuentas no cumplen la nomenclatura esperada, imprime una advertencia pero permite la continuacion del pipeline (comentado para confirmacion manual).

### `collectSecretsByTags(Map args)`

Recolecta secretos de AWS Secrets Manager en una cuenta y region especificas, filtrando por tags.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `credId` | String | Si | El ID de la credencial de Jenkins para autenticarse en AWS. | - |
| `region` | String | No | La region de AWS donde se buscaran los secretos. | `us-east-1` |
| `tagFiltersJson` | String | Si | Una cadena JSON que define los filtros de tags para la busqueda de secretos (ej. `'[{"Key":"Environment","Values":["dev"]}]'`). | - |

#### Retorno

Un mapa que contiene dos entradas:
- `text` (Map<String, String>): Un mapa de nombres de secretos (SecretString) a sus valores en texto plano.
- `binary` (Map<String, String>): Un mapa de nombres de secretos (SecretBinary) a sus valores en base64 plano.

### `printSummary(Map args)`

Imprime un resumen de los secretos recolectados, mostrando la cantidad y los nombres de los secretos de texto y binarios.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `secretsText` | Map | No | Mapa de secretos de texto (SecretString) a resumir. | `[:]` |
| `secretsBinary` | Map | No | Mapa de secretos binarios (SecretBinary) a resumir. | `[:]` |

### `pushSecretsWithTags(Map args)`

Publica o actualiza secretos en AWS Secrets Manager en una region de destino. Incluye logica de confirmacion manual en caso de detectar diferencias o cambios de tipo.

#### Parametros (`args` - Mapa)

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `credId` | String | Si | El ID de la credencial de Jenkins para autenticarse en AWS. | - |
| `region` | String | Si | La region de AWS donde se publicaran/actualizaran los secretos. | - |
| `secretsText` | Map | No | Mapa de nombres de secretos a sus valores (SecretString) para crear/actualizar. | `[:]` |
| `secretsBinary` | Map | No | Mapa de nombres de secretos a sus valores (SecretBinary) para crear/actualizar. | `[:]` |
| `destinoTagsNoBrackets` | String | No | Una cadena JSON que define los tags a aplicar a los secretos en destino, excluyendo los corchetes exteriores (ej. `{"Key":"estado","Value":"migrado"}`). | `{"Key":"estado","Value":"migrado"}` |
| `dryRun` | Boolean | No | Si es `true`, simula las operaciones sin realizar cambios reales en AWS Secrets Manager. | `false` |

### `congfigureSecrestsManagerFromJson(String filePath, boolean dryRun = true)`

Configura o actualiza masivamente secretos en AWS Secrets Manager a partir de un archivo JSON.

#### Descripcion

Esta funcion lee un archivo JSON con definiciones de secretos y procede a crear o actualizar estos secretos en AWS Secrets Manager. Soporta secretos de tipo `string` (JSON de clave-valor) y `binary` (contenido de un archivo). Proporciona un modo de ejecucion en seco (`dryRun`) para simular los cambios antes de aplicarlos.

#### Parametros

| Parametro | Tipo | Requerido | Descripcion | Valor por Defecto |
|---|---|---|---|---|
| `filePath` | String | Si | La ruta al archivo JSON que contiene la definicion de los secretos. | - |
| `dryRun` | Boolean | No | Si es `true`, la funcion simula las operaciones (creacion/actualizacion) sin realizar cambios reales en AWS Secrets Manager. Los cambios propuestos se mostraran en la consola y se exportaran a un archivo de diferencias. | `true` |

#### Formato del Archivo JSON de Entrada

El archivo JSON debe ser un array de objetos, donde cada objeto representa un secreto con los siguientes campos:

| Campo | Tipo | Requerido | Descripcion | Valores Permitidos para `type` |
|---|---|---|---|---|
| `name` | String | Si | El nombre completo del secreto en AWS Secrets Manager. | - |
| `description` | String | No | Una descripcion para el secreto. Por defecto: "N/A". | - |
| `type` | String | Si | El tipo de secreto. | `string`, `binary` |
| `keys` | List<String> | Condicional (para `type: string`) | Una lista de cadenas que representan las claves esperadas dentro del JSON del secreto. Si el secreto no existe, se creara con estas claves y valores vacios. Si existe, se añadiran las claves faltantes. | - |
| `file` | String | Condicional (para `type: binary`) | La ruta al archivo local cuyo contenido binario se usara para el secreto. | - |

**Ejemplo de `secrets.json`:**

```json
[
  {
    "name": "/mi-aplicacion/dev/db-credentials",
    "description": "Credenciales de base de datos para el entorno de desarrollo",
    "type": "string",
    "keys": ["username", "password", "host", "port"]
  },
  {
    "name": "/mi-aplicacion/dev/api-key-config",
    "description": "Configuracion de claves de API",
    "type": "string",
    "keys": ["api_key_google", "api_key_stripe"]
  },
  {
    "name": "/mi-aplicacion/dev/tls-certificate",
    "description": "Certificado TLS para el entorno de desarrollo",
    "type": "binary",
    "file": "certs/dev_cert.pem"
  }
]
```

#### Comportamiento

1.  **Lectura y Validacion**: Lee el archivo JSON y valida la estructura de cada entrada (presencia de `name`, `type`, y campos condicionales como `keys` o `file`).
2.  **Verificacion de Existencia**: Para cada secreto, intenta obtener su valor actual de AWS Secrets Manager.
3.  **Determinacion de Accion**:
    *   **Para `type: string`**:
        *   **CREATE**: Si el secreto no existe, se crea con las `keys` proporcionadas y valores vacios.
        *   **ADD_KEYS**: Si el secreto existe y se detectan nuevas `keys` en el JSON que no estan en el secreto actual, se añaden al secreto existente.
        *   **NO_CHANGE**: Si el secreto existe y todas las `keys` ya estan presentes.
    *   **Para `type: binary`**:
        *   **CREATE**: Si el secreto no existe, se crea con el contenido del `file` especificado.
        *   **NO_CHANGE**: Si el secreto ya existe, no se realiza ninguna accion (la funcion no compara el contenido binario para decidir si actualizar).
4.  **Modo Dry Run**: Si `dryRun` es `true`, la funcion solo imprime los iconos y mensajes de las acciones que **tomaria**, pero no ejecuta ningun comando `aws secretsmanager`.
5.  **Ejecucion de Cambios**: Si `dryRun` es `false`, la funcion ejecuta los comandos `aws secretsmanager create-secret` o `aws secretsmanager update-secret` segun la accion determinada.
6.  **Reporte de Diferencias**: Al finalizar, genera un archivo de diferencias en el workspace (ej. `secretsmanager-diff.json`), que detalla todos los secretos procesados, la accion determinada (`CREATE`, `ADD_KEYS`, `NO_CHANGE`), las claves añadidas (si aplica) y el estado.
7.  **Feedback Visual**: Utiliza una serie de iconos Unicode para indicar el progreso y el resultado de cada operacion en la consola de Jenkins.

#### Uso en un Pipeline

```groovy
stage('AWS Secrets Manager - Sincronizar desde JSON') {
    steps {
        script {
            // Asumiendo que 'configuration/dev/secrets.json' es la ruta al archivo JSON
            // y que 'SERVICE_CREDS' son tus credenciales de AWS y 'AWS_REGION' la region de destino.
            awsAuthFunctions.login(SERVICE_CREDS, AWS_REGION) {
                awsSecretsMigrationFunctions.congfigureSecrestsManagerFromJson(
                    "configuration/${env.ENVIRONMENT}/secrets.json",
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

**Tags:** `#awssecretsmanager`, `#secrets`, `#aws`, `#migration`, `#automation`, `#pipeline`