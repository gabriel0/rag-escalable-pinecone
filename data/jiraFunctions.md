# jiraFunctions — Libreria de integracion con Jira Cloud

Libreria para interactuar con la API REST de **Jira Cloud** (v2) desde pipelines de Jenkins.
Permite actualizar el estado de tickets, agregar comentarios y disparar automatizaciones.

---

## Requisitos previos

### Instancias de Jira Cloud

| Ambiente   | URL de la instancia                          |
|------------|----------------------------------------------|
| Sandbox    | `https://empresa-sandbox.atlassian.net`   |
| Produccion | `https://empresa.atlassian.net`           |

### Credencial Jenkins para operaciones REST

Crear una credencial de tipo **Username with password** en Jenkins por cada ambiente:

| Campo    | Valor                                                                   |
|----------|-------------------------------------------------------------------------|
| ID       | `jira-{ambiente}-api`  (ej: `jira-sbx-api`, `jira-prod-api`)          |
| Username | Email de la cuenta de servicio de Jira Cloud del ambiente              |
| Password | API Token de la cuenta de servicio (**no** la contrasena de la cuenta) |

> Generar el token en Jira Cloud: **Perfil > Cuenta > Seguridad > Tokens de API**

La libreria autentica con Basic Auth via curl:
```
curl -u "usuario-servicio:<api-token>" ...
```

> La Jira Cloud REST API requiere Basic Auth con `email:api_token`. No acepta Bearer token
> para tokens de API — ese formato es exclusivo de OAuth 2.0.
>
> Usar siempre la **cuenta de servicio** del ambiente correspondiente, no cuentas personales.

### Tokens para automatizaciones (webhooks)

Las URLs y tokens de los webhooks de Jira Automation estan almacenados directamente
en el mapa `JIRA_HOOKS_URLS` dentro de la libreria. **No se requieren credenciales
Jenkins para los webhooks.**

| Ambiente | Estado             |
|----------|--------------------|
| `sbx`    | Completo           |
| `prod`   | Pendiente de carga |

Si un tipo tiene `null` en URL o token para el ambiente solicitado, `dispararAutomatizacionPorTipo`
lanza error indicando que hay que completar el mapa. No existe fallback a credenciales Jenkins
para webhooks.

---

## Mapa de webhooks (`JIRA_HOOKS_URLS`)

La libreria incluye un mapa interno con las URLs y tokens secretos de los webhooks de Jira
Automation, organizados por ambiente y tipo. Cada tipo tiene una entrada de URL y una
entrada `_TOKEN` con el secreto de la regla.

```
JIRA_HOOKS_URLS = [
    sbx: [
        INIT_CONFIG                     : 'https://...',
        INIT_CONFIG_TOKEN               : '<secreto>',
        DEPLOYMENT_CONFIGS              : 'https://...',
        DEPLOYMENT_CONFIGS_TOKEN        : '<secreto>',
        REJECT_CONFIG                   : 'https://...',
        REJECT_CONFIG_TOKEN             : '<secreto>',
        INIT_ISSUE                      : 'https://...',
        INIT_ISSUE_TOKEN                : '<secreto>',
        REJECT_ISSUE                    : 'https://...',
        REJECT_ISSUE_TOKEN              : '<secreto>',
        BUG_CREATED                     : null,          // TBD
        DEPLOYMENT_TO_DESA              : 'https://...',
        DEPLOYMENT_TO_DESA_TOKEN        : '<secreto>',
        DEPLOYMENT_TO_TEST              : 'https://...',
        DEPLOYMENT_TO_TEST_TOKEN        : '<secreto>',
        CREATE_RELEASE                  : 'https://...',
        CREATE_RELEASE_TOKEN            : '<secreto>',
        ROLLBACK_RELEASE                : 'https://...',
        ROLLBACK_RELEASE_TOKEN          : '<secreto>',
        DEPLOYMENT_TO_UAT               : 'https://...',
        DEPLOYMENT_TO_UAT_TOKEN         : '<secreto>',
        DEPLOYMENT_TO_PROD              : 'https://...',
        DEPLOYMENT_TO_PROD_TOKEN        : '<secreto>',
        ACCEPT_DEPLOYMENT_TO_PROD       : 'https://...',
        ACCEPT_DEPLOYMENT_TO_PROD_TOKEN : '<secreto>',
        NORMALIZE_NON_PROD              : 'https://...',
        NORMALIZE_NON_PROD_TOKEN        : '<secreto>',
        DEPLOYMENT_ODDS_TO_PROD         : 'https://...',
        DEPLOYMENT_ODDS_TO_PROD_TOKEN   : '<secreto>'
    ],
    prod: [
        // Pendiente de carga
    ]
]
```

> Las URLs son formato **TOKEN_HEADER** (estandar Atlassian desde ene-2025): URL base sin token
> en el path. El token se envia en el header `X-Automation-Webhook-Token`.

---

## Funciones

### `dispararAutomatizacionPorTipo(params)` _(recomendado)_

Dispara una automatizacion de Jira Cloud buscando URL y token automaticamente por tipo y ambiente.

**Logica de resolucion:**
1. Lee `JIRA_HOOKS_URLS[ambiente][tipoAutomatizacion]` → URL del webhook.
2. Lee `JIRA_HOOKS_URLS[ambiente][tipoAutomatizacion + '_TOKEN']` → token secreto de la regla.
3. Si URL o token son `null` o no existen, lanza error indicando que hay que completar el mapa.
4. Si se proveen `issueKeys` y `data` no contiene `token`, lee automaticamente
   `issue.properties.token` del primer issue via `leerTokenIssue` y lo agrega al payload.
   - Si el payload usa formato anidado `data.data` (estilo `jira.sh`), se agrega en `data.data.token`.
   - Si el payload es plano, se agrega en `data.token`.

| Parametro          | Tipo        | Req. | Descripcion                                                                         |
|--------------------|-------------|------|-------------------------------------------------------------------------------------|
| tipoAutomatizacion | String      | Si   | Tipo en `UPPER_SNAKE_CASE`. Debe estar en `JIRA_AUTOMATION_TIPOS`                  |
| ambiente           | String      | No   | Ambiente a resolver en el mapa. Default: `'sbx'`                                   |
| issueKeys          | List/String | No   | Clave o lista de claves de tickets. Ej: `'PROJ-123'` o `['PROJ-123', 'PROJ-456']` |
| data               | Map         | No   | Datos adicionales en el payload (ej: `version`, `resultado`). Si incluye `token`, no se auto-resuelve |
| failOnError        | Boolean     | No   | Si `false`, loguea advertencia en lugar de lanzar error. Default: `true`            |

**Retorna:** `Boolean` — `true` si el webhook fue llamado exitosamente (HTTP 200/204).

**Tipos de automatizacion disponibles (`JIRA_AUTOMATION_TIPOS`):**

| Tipo                        | Descripcion                            |
|-----------------------------|----------------------------------------|
| `INIT_CONFIG`               | Inicializar configuracion              |
| `DEPLOYMENT_CONFIGS`        | Desplegar configuraciones              |
| `REJECT_CONFIG`             | Rechazar configuracion                 |
| `INIT_ISSUE`                | Inicializar issue                      |
| `REJECT_ISSUE`              | Rechazar issue                         |
| `BUG_CREATED`               | Bug creado (URL pendiente en sbx)      |
| `DEPLOYMENT_TO_DESA`        | Deploy a desarrollo                    |
| `DEPLOYMENT_TO_TEST`        | Deploy a testing                       |
| `CREATE_RELEASE`            | Crear release                          |
| `ROLLBACK_RELEASE`          | Rollback de release                    |
| `DEPLOYMENT_TO_UAT`         | Deploy a UAT                           |
| `DEPLOYMENT_TO_PROD`        | Deploy a produccion                    |
| `ACCEPT_DEPLOYMENT_TO_PROD` | Aceptar deploy a produccion            |
| `NORMALIZE_NON_PROD`        | Normalizar ambientes no productivos    |
| `DEPLOYMENT_ODDS_TO_PROD`   | Deploy impar a produccion              |

---

### `dispararAutomatizacion(params)`

Funcion de bajo nivel para disparar un webhook de Jira Automation con URL y token provistos
directamente. En uso normal se prefiere `dispararAutomatizacionPorTipo`, que resuelve
estos valores automaticamente desde el mapa interno.

Utiliza exclusivamente el modo **TOKEN_HEADER** (estandar vigente de Atlassian Cloud):
- URL base sin token en el path.
- Token enviado en el header `X-Automation-Webhook-Token`.

> Ref: [Configure the incoming webhook trigger in Atlassian Automation](https://support.atlassian.com/cloud-automation/docs/configure-the-incoming-webhook-trigger-in-atlassian-automation)

| Parametro    | Tipo        | Req. | Descripcion                                                                         |
|--------------|-------------|------|-------------------------------------------------------------------------------------|
| webhookUrl   | String      | Si   | URL base del webhook (sin token en el path)                                         |
| webhookToken | String      | Si   | Token secreto de la regla (`X-Automation-Webhook-Token`)                            |
| issueKeys    | List/String | No   | Clave o lista de claves de tickets. Ej: `'PROJ-123'` o `['PROJ-123', 'PROJ-456']` |
| data         | Map         | No   | Datos adicionales mergeados en el payload (ej: `token`, `status`, `message`)        |
| failOnError  | Boolean     | No   | Si `false`, loguea advertencia en lugar de lanzar error. Default: `true`            |

**Retorna:** `Boolean` — `true` si el webhook fue llamado exitosamente (HTTP 200/204).

**Formato del payload enviado:**

La funcion soporta ambos formatos de payload:

- **Plano** (campos a nivel raiz): `{{webhookData.campo}}`
- **Anidado estilo `jira.sh`** (objeto `data`): `{{webhookData.data.campo}}`

Ejemplo plano:

```json
{
  "issues": ["PROJ-123"],
  "token": "<issue.properties.token>",
  "status": "OK",
  "message": "Deploy completado"
}
```

Ejemplo anidado (compatible con automatizaciones que esperan formato `jira.sh`):

```json
{
  "issues": ["PROJ-123"],
  "data": {
    "token": "<issue.properties.token>",
    "repository": "mi-servicio",
    "status": "OK",
    "action": "deploy",
    "message": "[#123|https://jenkins/job/x/123/] - Se desplego correctamente en Test."
  }
}
```

---

### `leerTokenIssue(params)`

Lee la entity property `token` de un ticket de Jira Cloud (`issue.properties.token`).

Las reglas de automatizacion validan que `{{webhookData.token}}` coincida con
`{{issue.properties.token}}`. Esta funcion obtiene ese valor para incluirlo
en el payload del webhook. Es invocada automaticamente por `dispararAutomatizacionPorTipo`
cuando `data` no contiene el campo `token`.

| Parametro     | Tipo   | Req. | Descripcion                                                                     |
|---------------|--------|------|---------------------------------------------------------------------------------|
| issueKey      | String | Si   | Clave del ticket. Ej: `PROJ-123`                                                |
| ambiente      | String | No   | Ambiente para resolver `jiraUrl` y `credentialsId`. Default: `'sbx'`           |
| jiraUrl       | String | No   | URL base de la instancia. Si no se provee, se resuelve desde `ambiente`         |
| credentialsId | String | No   | ID de credencial Jenkins. Si no se provee, se resuelve como `jira-{ambiente}-api` |

**Retorna:** `String` con el valor del token, o `null` si la propiedad no existe o esta vacia.

**Comportamiento de validacion:**
- Si `issue.properties.token` no existe en el ticket → HTTP 404 → advertencia, retorna `null`.
- Si el valor es una lista vacia `[]` → advertencia, retorna `null`.
- Si el valor resulta vacio o solo espacios → advertencia, retorna `null`.
- En todos los casos de advertencia, `dispararAutomatizacionPorTipo` continua la ejecucion
  pero advierte que la regla de automatizacion podria rechazar el request.

---

### `obtenerTransiciones(params)`

Consulta y lista las transiciones de estado disponibles para un ticket.

| Parametro     | Tipo   | Req. | Descripcion                                                                       |
|---------------|--------|------|-----------------------------------------------------------------------------------|
| issueKey      | String | Si   | Clave del ticket. Ej: `PROJ-123`                                                  |
| ambiente      | String | No   | Ambiente para resolver `jiraUrl` y `credentialsId`. Default: `'sbx'`             |
| jiraUrl       | String | No   | URL base de Jira Cloud. Si no se provee, se resuelve desde `ambiente`             |
| credentialsId | String | No   | ID de credencial Jenkins (**Username with password**). Si no se provee, se resuelve como `jira-{ambiente}-api` |

**Retorna:** `List<Map>` con los campos `id`, `name` y `to.name` de cada transicion.

---

### `actualizarEstado(params)`

Aplica una transicion de estado a un ticket.
Puede resolver la transicion por nombre (`estadoDestino`) o aplicarla directamente por ID (`transitionId`).

| Parametro     | Tipo    | Req. | Descripcion                                                                       |
|---------------|---------|------|-----------------------------------------------------------------------------------|
| issueKey      | String  | Si   | Clave del ticket. Ej: `PROJ-456`                                                  |
| estadoDestino | String  | Si*  | Nombre del estado destino. Ej: `"In Progress"`, `"Done"` (insensible a mayusculas) |
| transitionId  | String  | Si*  | ID directo de la transicion. Tiene precedencia sobre `estadoDestino`              |
| ambiente      | String  | No   | Ambiente para resolver `jiraUrl` y `credentialsId`. Default: `'sbx'`             |
| jiraUrl       | String  | No   | URL base de Jira Cloud. Si no se provee, se resuelve desde `ambiente`             |
| credentialsId | String  | No   | ID de credencial Jenkins (**Username with password**). Si no se provee, se resuelve como `jira-{ambiente}-api` |
| failOnError   | Boolean | No   | Si `false`, loguea advertencia en lugar de lanzar error. Default: `true`          |

> (*) Se requiere al menos uno: `estadoDestino` o `transitionId`.

**Retorna:** `Boolean` — `true` si la transicion fue exitosa, `false` en caso contrario.

---

### `agregarComentario(params)`

Agrega un comentario a un ticket de Jira permitiendo elegir mecanismo:

- `hook` (**default**): dispara automatizacion Jira Cloud con payload estilo `jira.sh`.
- `api` (alternativo): usa REST API `/rest/api/2/issue/{issueKey}/comment`.

El texto soporta **Jira Wiki Markup**.

| Parametro     | Tipo    | Req. | Descripcion                                                                       |
|---------------|---------|------|-----------------------------------------------------------------------------------|
| issueKey      | String  | Si   | Clave del ticket. Ej: `PROJ-789`                                                  |
| comentario    | String  | Si*  | Texto del comentario. Soporta Jira Wiki Markup (*requerido en hook salvo casos con `data.message` o `action=rollback`) |
| ambiente      | String  | No   | Ambiente para resolver `jiraUrl` y `credentialsId`. Default: `'sbx'`             |
| jiraUrl       | String  | No   | URL base de Jira Cloud. Si no se provee, se resuelve desde `ambiente`             |
| credentialsId | String  | No   | ID de credencial Jenkins (**Username with password**). Si no se provee, se resuelve como `jira-{ambiente}-api` |
| visibility    | Map     | No   | Restriccion de visibilidad. Ej: `[type: 'role', value: 'Developers']`            |
| metodo        | String  | No   | `hook` (default) o `api`                                                          |
| fallbackApiOnHookError | Boolean | No | Si `true` y falla hook, intenta API automaticamente                              |
| tipoAutomatizacion | String | No | Tipo de hook (default: `DEPLOYMENT_TO_DESA`)                                     |
| action        | String  | No   | Solo hook OK. Default: `deploy`. Si `rollback`, arma mensaje de rollback por ambiente |
| status        | String  | No   | Solo hook. `OK` (default) o `ERROR`                                               |
| repository    | String  | No   | Solo hook. Nombre corto repo para `data.repository`                               |
| repoJiraPrefix| String  | No   | Solo hook. Si `repository` comienza con este prefijo, se elimina (equivalente a `${BITBUCKET_REPO_SLUG#$REPO_JIRA_PREFIX}`) |
| serverIds / entornos / servers | List/String | No | Solo hook. Lista o CSV de entornos para anexar al mensaje: `- Entornos: ...` |
| data          | Map     | No   | Solo hook. Permite enviar/override de `data` estilo `jira.sh`                     |
| failOnError   | Boolean | No   | Si `false`, loguea advertencia en lugar de lanzar error. Default: `true`          |

**Retorna:**
- Hook: `Boolean` (`true/false`)
- API: `String` con el ID del comentario creado
- En modo no bloqueante (`failOnError: false`) puede retornar `null` ante falla

---

### `agregarComentarioHook(params)`

Version explicita por webhook de automatizacion. Usa contrato de payload estilo `jira.sh`:

- `data.status`, `data.action`, `data.message` para casos OK
- `data.errors[].errorDesc` para casos ERROR
- `data.repository` y `data.token` (token auto-resuelto desde `issue.properties.token`)

Si `message` no se provee, genera prefijo build wiki: `[#BUILD_NUMBER|BUILD_URL] - ...`.
El texto por defecto de deploy/rollback se adapta segun `tipoAutomatizacion`/`ambiente` (no queda fijo en Desa).

Si no se provee `comentario` ni `data.message`, el mensaje se arma por accion (`action`) de forma equivalente al shell:

- `implementar` / `deploy` -> `Se desplego correctamente en <Ambiente>`
- `rollback` -> `Se realizo rollback correctamente en <Ambiente>`
- `devolver` -> `Se devolvio correctamente`
- cualquier otra -> `Accion <action> no reconocida`

Si se proveen `serverIds`/`entornos`/`servers`, agrega sufijo `- Entornos: ...`.

---

### `agregarComentarioApi(params)`

Version explicita por REST API de comentarios de Jira Cloud:

- Endpoint: `/rest/api/2/issue/{issueKey}/comment`
- HTTP esperado: `201`
- Soporta `visibility`

---

## Ejemplos de uso

### Disparar automatizacion por tipo (forma recomendada)

```groovy
// Ambiente sbx (default) — URL y token tomados del mapa JIRA_HOOKS_URLS
jiraFunctions.dispararAutomatizacionPorTipo(
    tipoAutomatizacion : 'DEPLOYMENT_TO_DESA',
    issueKeys          : params.JIRA_ISSUE_KEY
)
```

```groovy
// Con datos de contexto adicionales
jiraFunctions.dispararAutomatizacionPorTipo(
    tipoAutomatizacion : 'DEPLOYMENT_TO_TEST',
    ambiente           : 'sbx',
    issueKeys          : params.JIRA_ISSUE_KEY,
    data               : [
        ambiente : env.ENVIRONMENT,
        version  : env.CONTAINER_IMAGE_TAG,
        servicio : env.SERVICE_NAME,
        resultado: currentBuild.currentResult
    ],
    failOnError        : false
)
```

```groovy
// Ambiente prod (requiere que el mapa tenga las URLs cargadas)
jiraFunctions.dispararAutomatizacionPorTipo(
    tipoAutomatizacion : 'DEPLOYMENT_TO_PROD',
    ambiente           : 'prod',
    issueKeys          : params.JIRA_ISSUE_KEY
)
```

---

### Disparar con URL y token directos

```groovy
jiraFunctions.dispararAutomatizacion(
    webhookUrl   : 'https://api-private.atlassian.com/automation/webhooks/jira/a/<cloudId>/<ruleId>',
    webhookToken : '<secreto-de-la-regla>',
    issueKeys    : 'PROJ-123',
    data         : [status: 'OK', message: 'Deploy iniciado']
)
```

---

### Uso combinado en pipeline: automatizacion + comentario

```groovy
stage('Notificar Jira') {
    steps {
        script {
            jiraFunctions.dispararAutomatizacionPorTipo(
                tipoAutomatizacion : 'DEPLOYMENT_TO_DESA',
                issueKeys          : env.JIRA_ISSUE_KEY,
                data               : [version: env.CONTAINER_IMAGE_TAG, resultado: currentBuild.currentResult],
                failOnError        : false
            )
            jiraFunctions.agregarComentario(
                issueKey    : env.JIRA_ISSUE_KEY,
                ambiente    : 'sbx',
                comentario  : "Deploy completado: *${env.SERVICE_NAME}* v${env.CONTAINER_IMAGE_TAG} en *${env.ENVIRONMENT}*",
                failOnError : false
            )
        }
    }
}
```

---

### Consultar transiciones disponibles

```groovy
def transiciones = jiraFunctions.obtenerTransiciones(
    issueKey : 'PROJ-123',
    ambiente : 'sbx'
)
// transiciones = [[id:'11', name:'To Do', to:[name:'To Do']], [id:'21', name:'In Progress', ...], ...]
```

### Actualizar estado por nombre

```groovy
jiraFunctions.actualizarEstado(
    issueKey      : 'PROJ-456',
    estadoDestino : 'In Progress',
    ambiente      : 'sbx'
)
```

### Actualizar estado por ID de transicion (sin busqueda previa)

```groovy
jiraFunctions.actualizarEstado(
    issueKey     : 'PROJ-456',
    transitionId : '31',
    ambiente     : 'sbx'
)
```

### Agregar comentario (default hook, estilo `jira.sh`)

```groovy
jiraFunctions.agregarComentario(
    issueKey   : 'PROJ-789',
    ambiente   : 'sbx',
    tipoAutomatizacion: 'DEPLOYMENT_TO_TEST',
    comentario : 'Se desplego correctamente.',
    failOnError: false
)
```

### Hook sin comentario explicito (mensaje por `action`) y entornos

```groovy
jiraFunctions.agregarComentario(
    issueKey           : 'PROJ-789',
    ambiente           : 'sbx',
    tipoAutomatizacion : 'DEPLOYMENT_TO_TEST',
    action             : 'implementar',
    serverIds          : 'TEST01,TEST02',
    repoJiraPrefix     : 'alm-',
    failOnError        : false
)
```

### Agregar comentario via API (alternativo)

```groovy
jiraFunctions.agregarComentario(
    issueKey   : 'PROJ-789',
    metodo     : 'api',
    ambiente   : 'sbx',
    comentario : "Comentario por REST API.\nVersion: ${env.BUILD_TAG}",
    visibility : [type: 'role', value: 'Developers']
)
```

### Hook con fallback a API

```groovy
jiraFunctions.agregarComentario(
    issueKey              : 'PROJ-789',
    ambiente              : 'sbx',
    comentario            : 'Notificacion de despliegue',
    metodo                : 'hook',
    fallbackApiOnHookError: true,
    failOnError           : false
)
```

---

## Comportamiento general

- Las URLs y tokens de webhook estan en el mapa interno `JIRA_HOOKS_URLS`. No requieren credenciales Jenkins.
- Si un tipo tiene `null` en URL o token para el ambiente solicitado, `dispararAutomatizacionPorTipo` lanza error. No existe fallback a credenciales Jenkins para webhooks.
- Las credenciales Jenkins (`jira-{ambiente}-api`) se usan exclusivamente para operaciones REST (transiciones, comentarios API, lectura de propiedades de issue).
- `agregarComentario` usa `hook` por defecto; para API usar `metodo: 'api'` o `agregarComentarioApi`.
- En hook, `repository` puede sanitizarse removiendo `repoJiraPrefix`/`REPO_JIRA_PREFIX`.
- En hook, si no se envia `comentario`/`data.message`, el mensaje se construye automaticamente en base a `action`.
- Los archivos temporales de payload y respuesta se eliminan automaticamente al finalizar cada llamada (bloque `finally`).
- El parametro `failOnError: false` permite usar las funciones de forma no bloqueante (ideal para etapas de notificacion opcionales).
- Los nombres de estado en `estadoDestino` son insensibles a mayusculas/minusculas.
- Las credenciales nunca se exponen en logs gracias al uso de `set +x` y `withCredentials`.

---

## Endpoints Jira Cloud API v2 utilizados

| Funcion                  | Metodo | Endpoint                                                | HTTP esperado |
|--------------------------|--------|---------------------------------------------------------|---------------|
| `obtenerTransiciones`    | GET    | `/rest/api/2/issue/{issueKey}/transitions`              | 200           |
| `actualizarEstado`       | POST   | `/rest/api/2/issue/{issueKey}/transitions`              | 204           |
| `agregarComentario`      | POST   | `/rest/api/2/issue/{issueKey}/comment`                  | 201           |
| `leerTokenIssue`         | GET    | `/rest/api/2/issue/{issueKey}/properties/token`         | 200           |
| `dispararAutomatizacion` | POST   | Webhook URL de Jira Cloud Automation                    | 200 / 204     |

---

## Referencias

- https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues/#api-rest-api-2-issue-issueidorkey-transitions-post
- https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-comments/#api-rest-api-2-issue-issueidorkey-comment-post
- https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-properties/#api-rest-api-2-issue-issueidorkey-properties-propertykey-get
- https://support.atlassian.com/cloud-automation/docs/configure-the-incoming-webhook-trigger-in-atlassian-automation
