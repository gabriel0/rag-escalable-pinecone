# Funciones para Orquestar Escaneo con Gitleaks

Esta libreria (`gitLeaksFunctions.groovy`) actua como un orquestador para lanzar un pipeline secundario (sub-job) de Jenkins, el cual se encarga de realizar el escaneo de secretos en un repositorio de codigo utilizando **Gitleaks**.

Su proposito es centralizar la configuracion y la invocacion del escaneo, permitiendo que el pipeline principal delegue esta tarea de seguridad de forma asincrona.

## Metodos Principales

### `call(jobName, jobWait, jobPropagate, params)`

Este es el metodo principal que se invoca cuando se llama a la libreria. Su funcion es iniciar un sub-job de Jenkins, permitiendo configurar si se debe esperar o no a su finalizacion.

#### Parametros

| Parametro | Tipo | Requerido | Descripcion |
|---|---|---|---|
| `jobName` | String | Si | El nombre del pipeline de Jenkins que se va a ejecutar como sub-job. Este pipeline debe estar pre-configurado para realizar el escaneo con Gitleaks. |
| `jobWait` | Boolean | No | Si es `true`, el pipeline principal espera a que el sub-job termine. Por defecto es `false`. |
| `jobPropagate` | Boolean | No | Si es `true` y `jobWait` tambien es `true`, un fallo en el sub-job hara que el pipeline principal tambien falle. Por defecto es `false`. |
| `params` | Map | No | Un mapa de parametros que se pasaran al sub-job. Estos parametros son procesados por el metodo `gitLeaksParams` para establecer valores por defecto. |

#### Comportamiento

1.  **Transformacion de Parametros**: Convierte el mapa de Groovy (`params`) al formato de parametros que la funcion `build` de Jenkins requiere.
2.  **Invocacion del Sub-job**: Llama al `build job` utilizando los parametros `jobWait` y `jobPropagate` para controlar el flujo:
    *   `wait: jobWait`: Define si el pipeline principal espera (o no) a que el sub-job de Gitleaks termine.
    *   `propagate: jobPropagate`: Define si un fallo en el sub-job se propaga (o no) al pipeline principal.
3.  **Manejo de Errores**: Si la invocacion del sub-job falla (por ejemplo, si el job no existe), se captura la excepcion, se imprime un mensaje de advertencia en la consola y el pipeline principal continua su ejecucion sin detenerse.

### `gitLeaksParams(params)`

Este metodo auxiliar prepara el mapa de parametros que se enviara al sub-job. Su principal responsabilidad es tomar los parametros de entrada y asignarles valores por defecto si no se han especificado.

#### Parametros (`params` - Mapa)

Este metodo recibe el mapa `params` del metodo `call` y procesa las siguientes claves:

| Clave en `params` | Descripcion | Valor por Defecto |
|---|---|---|
| `repoToCheck` | Nombre del repositorio a escanear. | `dso-draft-biovalidacion` |
| `branchToCheck` | Rama del repositorio a escanear. | `develop` |
| `dojoProductType` | Tipo de producto en DefectDojo. | `infraestructura` |
| `dojoProductName` | Nombre del producto en DefectDojo. | `dso-draft-biovalidacion` |
| `dojoEngagementName`| Nombre del "engagement" en DefectDojo. | `candidate` |
| `jiraServiceUser` | Usuario de servicio para la integracion con JIRA. | `usuario-servicio` |
| `jiraProjectKey` | Clave del proyecto en JIRA donde se crearan las incidencias. | `SDR` |
| `jiraIssueType` | Tipo de incidencia a crear en JIRA. | `bug` |
| `jiraDefaultAssigneeUser` | Email del usuario asignado por defecto a las incidencias. | `usuario-servicio` |
| `jiraFpAssigneeUser` | Email para asignar incidencias marcadas como Falsos Positivos. | (vacio) |
| `jiraHrAssigneeUser` | Email para asignar incidencias marcadas como de Alto Riesgo. | (vacio) |
| `jiraReviewAssigneeUser` | Email para asignar incidencias que requieren revision. | (vacio) |
| `secretToClone` | Nombre del secreto de Jenkins que contiene las credenciales para clonar el repositorio. | (vacio) |
| `stack` | Stack tecnologico de la aplicacion (ej. `java`, `nodejs`). | (vacio) |

#### Retorno

-   **Exito**: Devuelve un nuevo mapa (`paramsJob`) con todas las claves y sus valores (ya sean los proporcionados o los por defecto), listo para ser enviado al sub-job.
-   **Fallo**: Si ocurre un error durante el procesamiento de los parametros, se imprime un mensaje de advertencia en la consola y se devuelve un mapa vacio (`[:]`) para prevenir que el sub-job se inicie con parametros incorrectos.

## Uso en un Pipeline

El siguiente ejemplo muestra como se invocaria esta libreria desde un `Jenkinsfile` para lanzar un escaneo de Gitleaks en un pipeline llamado `gitleaks-scanner-job`.

```groovy
stage('Security - Disparar Escaneo de Secretos') {
    steps {
        script {
            // Llama a la libreria para iniciar el sub-job de Gitleaks
            gitLeaksFunctions(
                jobName: 'gitleaks-scanner-job', // Nombre del pipeline que hace el escaneo
                jobWait: false,                  // No esperar a que termine
                jobPropagate: false,             // No fallar este pipeline si el sub-job falla
                params: [
                    repoToCheck: 'mi-repositorio-importante',
                    branchToCheck: 'main',
                    secretToClone: 'credenciales-git-ssh'
                ]
            )
            echo "El sub-job de escaneo de secretos ha sido iniciado en segundo plano."
        }
    }
}
```

**Tags:** `#gitleaks`, `#security`, `#secrets`, `#subjob`, `#orchestration`
