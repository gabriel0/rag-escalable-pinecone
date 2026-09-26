# Validaciones Cloud (cloudValidationFunctions)

Libreria que centraliza las validaciones previas al despliegue segun el proveedor cloud y el orquestador configurados. Actua como un **dispatcher por sabor**: el pipeline invoca siempre `validate()` sin conocer los detalles del proveedor, y la libreria despacha la logica correcta.

## Sabores soportados

| Cloud | Orquestador | Validaciones |
|-------|-------------|--------------|
| `aws` | `eks`       | ECR (repositorio + cifrado KMS) + CloudWatch Logs Insights |
| `aws` | `ecs`       | ECR (repositorio + cifrado KMS) |
| `gcp` | `gke`/`helm`| Pendiente de implementacion |
| cualquiera | `standalone` | Omitido (sin registry cloud) |

> **Nota sobre CW Logs Insights y ECS:** en ECS el log group se define en la task definition; no es necesario gestionarlo desde el pipeline. Por eso `manageLogQuery` solo se ejecuta para orquestadores que no sean `ecs`.

---

## `validate`

Punto de entrada principal. Determina el proveedor cloud y el orquestador activos y despacha las validaciones correspondientes.

### Parametros

Todos son opcionales; si no se pasan, se resuelven desde variables de entorno.

| Parametro        | Variable de entorno   | Descripcion                                              |
|------------------|-----------------------|----------------------------------------------------------|
| `cloud`          | `DEPLOY_CLOUD`        | Proveedor cloud (`aws`, `gcp`). Default: `aws`           |
| `orchestrator`   | `DEPLOY_ORCHESTRATOR` | Orquestador (`eks`, `ecs`, `gke`, `helm`, `standalone`)  |
| `credId`         | `SERVICE_CREDS`       | ID de credencial Jenkins para el proveedor cloud         |
| `dockerRegistry` | `DOCKER_PIPELINE_RUN` | Registry del contenedor pipeline (usado como runtime)    |
| `dockerImage`    | `DOCKER_PIPELINE_IMAGE`| Imagen del contenedor pipeline                          |

### Variables de entorno consumidas internamente

- `ECR_REPOSITORY`: repositorio ECR donde se valida la imagen.
- `IMAGE_NAME`: nombre de la imagen a validar.
- `KMS_KEYID_ARN`: ARN de la clave KMS para verificar el cifrado del repositorio ECR.
- `ENVIRONMENT`: ambiente de despliegue (`dev`, `test`, `prod`, etc.).
- `SERVICE_NAME`: nombre del servicio (para CW Logs Insights).
- `NAMESPACE`: namespace Kubernetes (para CW Logs Insights en EKS).

### Logica de ejecucion

1. Resuelve `cloud`, `orchestrator` y credenciales desde parametros o variables de entorno.
2. Si `orchestrator == 'standalone'`, registra un mensaje informativo y retorna sin hacer nada.
3. Segun el valor de `cloud`, despacha a `_validateAws` o `_validateGcp`.
4. Si el proveedor no tiene implementacion, registra un aviso y continua sin error.

### Ejemplo de uso en Jenkinsfile

```groovy
stage('Validaciones Cloud') {
    when {
        expression { env.PIPELINE_SCOPE.contains("cd") && env.IMAGE_NAME?.trim() }
    }
    steps {
        script {
            statsFunctions.recordStageTiming("validaciones_cloud") {
                cloudValidationFunctions.validate()
            }
        }
    }
}
```

Pasando parametros explicitamente (util para testing o pipelines con credenciales alternativas):

```groovy
cloudValidationFunctions.validate(
    cloud      : 'aws',
    credId     : 'mi-credencial-aws',
    orchestrator: 'eks'
)
```

---

## `_validateAws` (privado)

Ejecuta las validaciones especificas para AWS dentro de un contenedor pipeline con credenciales AWS inyectadas.

### Validaciones ejecutadas

1. **ECR — `awsEcrFunctions.mainEcr`**
   - Verifica que el repositorio `${ECR_REPOSITORY}/${IMAGE_NAME}` exista en ECR.
   - Verifica que el repositorio tenga cifrado KMS configurado con `KMS_KEYID_ARN`.
   - Se ejecuta para todos los orquestadores AWS (`eks`, `ecs`, `helm`).

2. **CloudWatch Logs Insights — `awsLogsFunctions.manageLogQuery`**
   - Crea o actualiza el log group y las queries guardadas de CW Logs Insights.
   - Se ejecuta **solo si el orquestador no es `ecs`** (en ECS el log group se gestiona en la task definition).

### Manejo de errores

Si cualquiera de las validaciones falla, se establece `env.MENSAJE` con un mensaje descriptivo y el pipeline aborta con `error()`.

---

## `_validateGcp` (privado)

Placeholder para futuras validaciones GCP. Actualmente registra un mensaje informativo y continua sin error.

### Implementaciones futuras sugeridas

- Verificar que la imagen exista en **Artifact Registry**.
- Validar permisos de **Workload Identity** para el service account del pod.
- Verificar que el cluster GKE este activo y accesible.
- Validar cuotas de recursos en el proyecto GCP.

### Como implementar

```groovy
private def _validateGcp(String orchestrator, String credId) {
    withCredentials([file(credentialsId: credId, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
        sh "gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS"
        // validaciones especificas segun orchestrator (gke, helm, etc.)
    }
}
```

---

## Como agregar un nuevo proveedor

1. Agregar un `case` en el `switch` de `validate()`:

```groovy
case 'azure':
    _validateAzure(orchestrator, credId, dockerReg, dockerImg)
    break
```

2. Implementar el metodo privado correspondiente:

```groovy
private def _validateAzure(String orchestrator, String credId, String dockerReg, String dockerImg) {
    // logica de validacion para Azure Container Registry, AKS, etc.
}
```

Los pipelines no requieren ningun cambio.
