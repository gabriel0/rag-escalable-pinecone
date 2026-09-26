# jenkinsFunctions.groovy

Funciones utilitarias para gestionar pipelines y carpetas de Jenkins desde una Shared Library.

## Alcance

Este modulo permite:

- Descargar el `config.xml` de un job plantilla.
- Obtener crumb CSRF para operaciones `POST`.
- Validar si existen jobs/carpetas de Jenkins.
- Crear carpetas Jenkins faltantes en una ruta jerarquica.
- Crear un pipeline nuevo a partir de un template XML.
- Capturar metadatos SCM del job y exponerlos por `env`.

---

## Funciones

### `getTemplate(String url, String token, String user)`

Descarga el `config.xml` de un job plantilla y lo guarda localmente como `template.xml`.

**Parametros**
- `url`: URL base del job plantilla (sin `/config.xml`).
- `token`: API token con permisos de lectura.
- `user`: Usuario Jenkins.

**Salida**
- No retorna un valor funcional; su efecto es generar `template.xml`.

---

### `getCrumb(String token, String user, String jenkinsServerUrl)`

Obtiene el crumb de Jenkins para proteger llamadas `POST` contra CSRF.

**Parametros**
- `token`: API token del usuario.
- `user`: Usuario Jenkins.
- `jenkinsServerUrl`: URL base del Jenkins objetivo.

**Salida**
- Lista de dos elementos: `[crumbField, crumbValue]`.

---

### `createPipelineFromTemplate(String urlNewPipeline, String crumbField, String crumbValue, String token, String user)`

Crea un job/pipeline usando el archivo `template.xml`. La URL final de creacion se construye como:

- `<pipelineDir>/createItem?name=<pipelineName>`

Donde `pipelineDir` y `pipelineName` se obtienen desde `urlNewPipeline`.

**Parametros**
- `urlNewPipeline`: URL completa del pipeline nuevo.
- `crumbField`: Nombre del header de crumb CSRF.
- `crumbValue`: Valor del crumb CSRF.
- `token`: API token del usuario destino.
- `user`: Usuario Jenkins destino.

**Salida**
- Retorna la salida estandar de `curl`.

---

### `guaranteeJenkinsPipelinePath(String token, String user, String urlNewPipeline)`

Valida que exista la ruta de carpetas Jenkins para el pipeline destino. Si alguna carpeta intermedia no existe, la crea secuencialmente.

**Parametros**
- `token`: API token con permisos de consulta/creacion.
- `user`: Usuario Jenkins.
- `urlNewPipeline`: URL completa del pipeline a crear.

**Salida**
- `true`: la ruta queda valida.
- `false`: no se pudo validar/crear correctamente la ruta.

---

### `jenkinsDirOrPipeExist(String token, String user, String jenkinsDirOrPipe)`

Valida existencia de carpeta/job Jenkins mediante `GET <url>/api/json`.

**Parametros**
- `token`: API token.
- `user`: Usuario Jenkins.
- `jenkinsDirOrPipe`: URL de carpeta o pipeline.

**Salida**
- `true` si el HTTP code es `200`.
- `false` para cualquier otro codigo.

---

### `setupNewJenkinsPipeline(String urlTemplate, String urlNewPipeline, String token, String user, String jenkinsServerUrl)`

Flujo principal de alta de pipeline:

1. Verifica que el pipeline no exista.
2. Verifica que no se cree en raiz (debe tener al menos una carpeta).
3. Garantiza/crea la ruta de carpetas (`guaranteeJenkinsPipelinePath`).
4. Obtiene crumb (`getCrumb`).
5. Descarga template (`getTemplate`).
6. Crea el pipeline (`createPipelineFromTemplate`).

Si no puede crear, registra mensajes informativos en `env.MENSAJE` y lanza `error` ante excepciones.

**Parametros**
- `urlTemplate`: URL del job plantilla origen.
- `urlNewPipeline`: URL del pipeline destino.
- `token`: API token del usuario.
- `user`: Usuario Jenkins.
- `jenkinsServerUrl`: URL base del Jenkins destino.

---

### `captureJobScmMetadata()`

Resuelve metadatos SCM del job actual y los persiste en variables de entorno para trazabilidad.

**Variables de entorno definidas**
- `CONFIGURED_BRANCH_SPECIFIER`: branch specifier configurado en el job.
- `INVOKED_SCRIPT_PATH`: Jenkinsfile/ruta de script resuelta.
- `INVOKED_SCRIPT_PATH_SOURCE`: origen del `scriptPath` (`job_definition`, `scm`, `fallback_default`).

**Notas**
- Debe ejecutarse en contexto de pipeline (acceso a `scm` y `currentBuild`).
- Es idempotente y tolerante a propiedades no disponibles segun tipo de job.

---

## Ejemplo de uso

```groovy
@Library('devops-library-commons') _

pipeline {
  agent any
  stages {
    stage('Crear pipeline Jenkins') {
      steps {
        script {
          setupNewJenkinsPipeline(
            'https://jenkins.example.com/job/template-job',
            'https://jenkins.example.com/job/team/job/proyecto/job/mi-pipeline',
            env.JENKINS_TOKEN,
            env.JENKINS_USER,
            'https://jenkins.example.com'
          )
        }
      }
    }
  }
}
```

---

## Recomendaciones

- Proteger `token` y `user` con credenciales de Jenkins (`withCredentials`).
- Revisar permisos para consultar, crear carpetas y crear jobs.
- El uso de `curl -k` deshabilita validacion estricta TLS; idealmente usar certificados confiables.
