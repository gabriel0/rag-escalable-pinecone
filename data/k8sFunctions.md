# k8sFunctions

Biblioteca de funciones para gestionar despliegues y operaciones en Kubernetes (EKS) desde pipelines de Jenkins.

## Descripcion

Este conjunto de funciones proporciona utilidades completas para trabajar con Kubernetes en AWS EKS, incluyendo despliegue de manifiestos, gestion de Helm charts, manejo de CronJobs, troubleshooting automatico, y operaciones de rollout/rollback.

---

## Funciones

### Helm Functions

#### helmInstall

Instala o actualiza un Helm chart en Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| aMicroserviceDeployFlag | String | Si | Flag para desplegar microservicio ("true"/"false") |
| aNsConfigDeployFlag | String | Si | Flag para desplegar configuracion de namespace ("true"/"false") |

##### Variables de Entorno Requeridas

- `CREDENTIAL_NEXUS`: ID de credencial de Nexus
- `HELM_CHART_REGISTRY_URL`: URL del registro de Helm charts
- `HELM_CHART_REGISTRY_FILENAME`: Nombre del archivo del chart
- `HELM_CHART_DEPLOY_NAME`: Nombre del despliegue Helm
- `NAMESPACE`: Namespace de Kubernetes
- `ENV_NAME`: Nombre del ambiente (dev, pre, prod)
- `SHARED_CONFIG_APP_GROUP`: Grupo de aplicacion para config compartida
- `DOCKER_IMAGE_SINGLE_NAME`: Nombre de la imagen Docker
- `DOCKER_GCP_IMAGE_NAME`: Ruta completa de la imagen en el registro
- `DOCKER_IMAGE_TAG`: Tag de la imagen Docker
- `MICROSERVICE_NAME`: Nombre del microservicio

##### Ejemplo

```groovy
stage('Deploy Helm') {
    steps {
        script {
            k8sFunctions.helmInstall('true', 'false')
        }
    }
}
```

---

#### helmList

Lista los Helm releases en el namespace configurado.

##### Ejemplo

```groovy
k8sFunctions.helmList()
```

---

#### helmTemplate

Genera el template del Helm chart sin aplicarlo.

##### Ejemplo

```groovy
k8sFunctions.helmTemplate()
```

---

#### helmUninstall

Desinstala un Helm release del namespace configurado.

##### Ejemplo

```groovy
k8sFunctions.helmUninstall()
```

---

#### helmTasks

Ejecuta la operacion Helm. `helmInstall`, `helmList`, `helmTemplate` y `helmUninstall` delegan en este metodo.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| command | String | Si | `install`, `template`, `uninstall` o `list` |
| aMicroserviceDeployFlag | String | Si | Solo en `install`. `"true"` aplica el microservicio |
| aNsConfigDeployFlag | String | Si | Solo en `install`. `"true"` aplica la config compartida del namespace |

##### Comportamiento

- `install` y `template`: descargan `${HELM_CHART_REGISTRY_URL}/${HELM_CHART_REGISTRY_FILENAME}` con `CREDENTIAL_NEXUS`.
- `template`: `helm template` del chart descargado. No lo aplica.
- `uninstall`: `helm uninstall ${HELM_CHART_DEPLOY_NAME}` en `NAMESPACE`.
- `install` con `aNsConfigDeployFlag=true`: `helm upgrade --install` usando `nsSharedConfigs/${SHARED_CONFIG_APP_GROUP}/nsSharedConfig_${ENV_NAME}_values.yaml`, con `workload.enable=false` y `nsSharedConfig.enable=true`.
- `install` con `aMicroserviceDeployFlag=true`: `helm upgrade --install` del release `${HELM_CHART_DEPLOY_NAME}-${DOCKER_IMAGE_SINGLE_NAME}` usando `helmValues/${MICROSERVICE_NAME}_${ENV_NAME}_values.yaml`, imagen `DOCKER_GCP_IMAGE_NAME` y tag `DOCKER_IMAGE_TAG`.
- `list`: `helm list --namespace=${NAMESPACE}`.

Los dos flags de `install` son independientes: pueden ejecutarse los dos, uno o ninguno.

##### Variables de entorno

Las mismas que `helmInstall`: `CREDENTIAL_NEXUS`, `HELM_CHART_REGISTRY_URL`, `HELM_CHART_REGISTRY_FILENAME`, `HELM_CHART_DEPLOY_NAME`, `NAMESPACE`, `ENV_NAME`, `SHARED_CONFIG_APP_GROUP`, `DOCKER_IMAGE_SINGLE_NAME`, `DOCKER_GCP_IMAGE_NAME`, `DOCKER_IMAGE_TAG`, `MICROSERVICE_NAME`.

##### Retorna

No retorna valor.

##### Ejemplo

```groovy
k8sFunctions.helmTasks('install', 'true', 'false')
k8sFunctions.helmTasks('list', 'false', 'false')
```

---

### Kubernetes Deployment Functions

#### deployUnifiedManifest

Realiza el despliegue unificado de manifiestos en Kubernetes con validaciones, rollback automatico y troubleshooting.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| clusterName | String | Si | Nombre del cluster de EKS |
| k8sDeployPath | String | Si | Ruta donde se encuentra el YAML unificado |
| imageName | String | Si | Nombre del deployment/microservicio |
| nameSpace | String | Si | Namespace donde crear los recursos |
| awsRegion | String | Si | Region de AWS (ej: "us-east-1") |
| imageTag | String | No | Tag de la imagen (default: env.CONTAINER_IMAGE_TAG) |
| retries | Integer | No | Numero de reintentos (default: 5) |
| delay | Integer | No | Delay entre reintentos en segundos (default: 12) |

##### Proceso de Ejecucion

1. Valida endpoint de AWS EKS
2. Configura kubeconfig para el cluster
3. Verifica workers disponibles
4. Crea namespace si no existe
5. Valida y limpia ReplicaSets antiguos
6. Aplica el manifiesto (con modo forzado opcional)
7. Verifica existencia del deployment
8. Realiza rollout si la version es la misma
9. Verifica estado del rollout con timeout
10. En caso de fallo: obtiene logs, realiza rollback (salvo `K8S_ROLLBACK=false`) y recopila debug info

##### Variables de Entorno Especiales

- `FORCE_K8S_DEPLOY="true"`: Activa modo forzado (elimina y reaplica)
- `K8S_ROLLBACK="false"`: Omite el rollback ante un fallo de rollout y deja la version fallida. Si no esta definida, o tiene otro valor, se hace rollback
- `READINESS_FAILURE_TH`: Umbral de fallos de readiness probe
- `READINESS_PERIOD_SEC`: Periodo de readiness probe
- `READINESS_TIMEOUT_SEC`: Timeout de readiness probe
- `READINESS_INITIAL_DELAY`: Delay inicial de readiness probe

##### Ejemplo

```groovy
stage('Deploy to Production') {
    steps {
        script {
            k8sFunctions.deployUnifiedManifest(
                clusterName: 'production-cluster',
                k8sDeployPath: './k8s',
                imageName: 'mi-api',
                nameSpace: 'production',
                awsRegion: 'us-east-1',
                imageTag: '1.0.0',
                retries: 5,
                delay: 12
            )
        }
    }
}
```

---

#### deployUnifiedCronJob

Despliega o actualiza un CronJob unificado en Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| clusterName | String | Si | Nombre del cluster de EKS |
| k8sDeployPath | String | Si | Ruta del manifiesto YAML |
| cronJobName | String | Si | Nombre del CronJob |
| nameSpace | String | Si | Namespace donde crear el CronJob |
| awsRegion | String | Si | Region de AWS |
| imageTag | String | Si | Tag de la imagen a desplegar |
| retries | Integer | No | Numero de reintentos (default: 5) |
| delay | Integer | No | Delay entre reintentos (default: 12) |

##### Proceso de Ejecucion

1. Configura acceso al cluster EKS
2. Verifica workers disponibles
3. Asegura que el namespace exista
4. Aplica el manifiesto del CronJob
5. Verifica la actualizacion del CronJob
6. En caso de fallo: recopila debug info

##### Ejemplo

```groovy
k8sFunctions.deployUnifiedCronJob(
    clusterName: 'production-cluster',
    k8sDeployPath: './k8s',
    cronJobName: 'data-sync-job',
    nameSpace: 'production',
    awsRegion: 'us-east-1',
    imageTag: '1.0.0'
)
```

---

#### deployOrchestrator

Funcion orquestadora que determina si el despliegue es de Deployment o CronJob basandose en variables de entorno.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| clusterName | String | Si | Nombre del cluster de EKS |
| k8sDeployPath | String | Si | Ruta del manifiesto |
| resourceName | String | Si | Nombre del recurso |
| nameSpace | String | Si | Namespace |
| awsRegion | String | Si | Region de AWS |
| imageTag | String | Si | Tag de la imagen |

##### Logica de Decision

- Si `env.CRONJOB_SCHEDULE` esta definido y no vacio → Despliega CronJob
- Caso contrario → Despliega Deployment

##### Ejemplo

```groovy
k8sFunctions.deployOrchestrator(
    clusterName: 'my-cluster',
    k8sDeployPath: './k8s',
    resourceName: 'my-service',
    nameSpace: 'production',
    awsRegion: 'us-east-1',
    imageTag: '1.0.0'
)
```

---

### Configuration Functions

#### configUnifiedEks

Configura el kubeconfig para un cluster EKS especifico con reintentos automaticos.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| clusterName | String | Si | Nombre del cluster de EKS |
| awsRegion | String | No | Region de AWS (default: "us-east-1") |

##### Caracteristicas

- Intenta hasta 6 veces con delay de 10 segundos
- Timeout de 30 segundos por intento
- Valida endpoint de AWS antes de cada intento

##### Ejemplo

```groovy
k8sFunctions.configUnifiedEks('production-cluster', 'us-east-1')
```

---

#### nameSpaceUnified

Crea un namespace en Kubernetes si no existe.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| namespace | String | Si | Nombre del namespace |

##### Ejemplo

```groovy
k8sFunctions.nameSpaceUnified('production')
```

---

### Manifest Operations

#### applyManifest

Aplica un manifiesto de Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| deploymentFile | String | Si | Ruta del archivo de manifiesto |

##### Ejemplo

```groovy
k8sFunctions.applyManifest('./k8s/mi-api-manifiesto.yaml')
```

---

#### deleteManifest

Elimina recursos mediante un manifiesto de Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| deploymentFile | String | Si | Ruta del archivo de manifiesto |

##### Ejemplo

```groovy
k8sFunctions.deleteManifest('./k8s/mi-api-manifiesto.yaml')
```

---

### Deployment Operations

#### performRollingUpdate

Realiza un rolling update (restart) de un deployment en Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace del deployment |

##### Ejemplo

```groovy
k8sFunctions.performRollingUpdate('mi-api', 'production')
```

---

#### performRollbackUpdate

Realiza un rollback a la version anterior de un deployment.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace del deployment |

##### Comportamiento

- Verifica que exista mas de una revision antes de hacer rollback
- Si solo hay una revision, no ejecuta el rollback

##### Ejemplo

```groovy
k8sFunctions.performRollbackUpdate('mi-api', 'production')
```

---

#### performScaleDeploy

Escala un deployment a un numero especifico de replicas.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| deployName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace del deployment |
| replicas | Integer | Si | Numero de replicas (0, 1, 2, 3, etc.) |

##### Ejemplo

```groovy
k8sFunctions.performScaleDeploy('mi-api', 'production', 3)
```

---

#### restartPods

Ejecuta el restart de deployments de manera ordenada.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| deploymentName | String | Si | Nombres de deployments separados por espacios |
| nameSpace | String | Si | Namespace del deployment |
| clusterName | String | Si | Nombre del cluster EKS |
| awsRegion | String | Si | Region de AWS |

##### Ejemplo

```groovy
k8sFunctions.restartPods(
    'mi-api mi-frontend',
    'production',
    'prod-cluster',
    'us-east-1'
)
```

---

### Verification Functions

#### checkDeploymentExists

Valida si un deployment existe en Kubernetes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace |

##### Retorna

`Boolean` - `true` si el deployment existe, `false` en caso contrario.

##### Ejemplo

```groovy
if (k8sFunctions.checkDeploymentExists('mi-api', 'production')) {
    println "Deployment existe"
}
```

---

#### verifyRolloutStatus

Verifica el estado del rollout de un deployment con timeout calculado basado en readiness probes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace |

##### Calculo del Timeout

El timeout se calcula usando: `initialDelay + (failureThreshold + 1) * (periodSeconds + timeoutSeconds)`

##### Retorna

`Boolean` - `true` si el rollout se completo correctamente.

##### Ejemplo

```groovy
if (k8sFunctions.verifyRolloutStatus('mi-api', 'production')) {
    println "Rollout exitoso"
} else {
    error "Rollout fallo"
}
```

---

#### checkAvailableWorkers

Valida si hay workers disponibles en el cluster de Kubernetes.

##### Retorna

`Integer` - 0 si hay al menos un worker, 1 si no hay workers.

##### Ejemplo

```groovy
if (k8sFunctions.checkAvailableWorkers() == 0) {
    println "Hay workers disponibles"
}
```

---

#### verifyCronJobUpdate

Verifica que un CronJob se haya actualizado con una etiqueta de imagen especifica.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| cronJobName | String | Si | Nombre del CronJob |
| namespace | String | Si | Namespace |
| expectedImageTag | String | Si | Tag de imagen esperado |
| retries | Integer | Si | Numero de reintentos |
| delay | Integer | Si | Delay entre reintentos |

##### Ejemplo

```groovy
k8sFunctions.verifyCronJobUpdate(
    'data-sync-job',
    'production',
    '1.0.0',
    5,
    10
)
```

---

### Information Retrieval Functions

#### getVersionDeploy

Obtiene la version (tag) de la imagen utilizada en un deployment.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre del deployment |
| namespace | String | Si | Namespace |

##### Retorna

`String` - El tag de la imagen (ej: "1.0.0").

##### Ejemplo

```groovy
def currentVersion = k8sFunctions.getVersionDeploy('mi-api', 'production')
println "Version actual: ${currentVersion}"
```

---

#### getFailedPodLogs

Obtiene e imprime los logs de un pod fallido.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| imageName | String | Si | Nombre de la aplicacion |
| namespace | String | Si | Namespace |

##### Caracteristicas

- Busca pods con selector `app=${imageName}`
- Intenta obtener logs previos (--previous)
- Si no hay logs previos, muestra logs actuales
- Muestra hasta 100 lineas

##### Ejemplo

```groovy
k8sFunctions.getFailedPodLogs('mi-api', 'production')
```

---

### ReplicaSet Management

#### validateSingleReplicaSet

Valida que un Deployment tiene solo un ReplicaSet activo.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| namespace | String | Si | Namespace |
| deployment | String | Si | Nombre del Deployment |

##### Retorna

`Boolean` - `true` si hay 0 o 1 ReplicaSet activo.

##### Ejemplo

```groovy
if (!k8sFunctions.validateSingleReplicaSet('production', 'mi-api')) {
    k8sFunctions.removeOldReplicaSet('production', 'mi-api')
}
```

---

#### removeOldReplicaSet

Elimina el ReplicaSet mas antiguo dejando solo el mas actual activo.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| namespace | String | Si | Namespace |
| deployment | String | Si | Nombre del Deployment |

##### Ejemplo

```groovy
k8sFunctions.removeOldReplicaSet('production', 'mi-api')
```

---

### Debugging and Troubleshooting

#### gatherK8sDebugInfo

Recolecta informacion completa de depuracion para un deployment fallido.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params.namespace | String | Si | Namespace de Kubernetes |
| params.deploymentName | String | Si | Nombre del deployment |
| params.clusterName | String | Si | Nombre del cluster EKS |

##### Informacion Recopilada

1. **Eventos del namespace** (ordenados por timestamp)
2. **Deployment**: Descripcion y JSON
3. **ReplicaSets**: Lista, descripcion y YAML de los 3 mas recientes
4. **Pods de ReplicaSets**: Logs y descripcion de pods de los 3 RS mas recientes
5. **Servicio**: Identificacion y descripcion del servicio asociado
6. **Ingress**: Identificacion y descripcion del ingress asociado
7. **Pod activo actual**: Descripcion, logs actuales y logs previos

##### Archivos Generados

- `EVENTS_${deploymentName}-${namespace}.log`
- `DEPLOYMENTINFO_${deploymentName}-${namespace}.log`
- `REPLICASETINFO_${deploymentName}-${namespace}.log`
- `PODINFO_ACTIVE_${deploymentName}-${namespace}.log`
- `PODLOGS_ACTIVE_CURRENT_${deploymentName}-${namespace}.log`
- `PODLOGS_ACTIVE_PREVIOUS_${deploymentName}-${namespace}.log`
- `PODLOGS_FROM_RS_HASH_${hash}_${deploymentName}-${namespace}.log`
- `PODINFO_FROM_RS_HASH_${hash}_${deploymentName}-${namespace}.log`
- `INGRESSINFO_${deploymentName}-${namespace}.log`

##### Ejemplo

```groovy
k8sFunctions.gatherK8sDebugInfo(
    namespace: 'production',
    deploymentName: 'mi-api',
    clusterName: 'prod-cluster'
)
```

---

#### gatherCronJobDebugInfo

Recolecta informacion de depuracion para un CronJob fallido.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params.namespace | String | Si | Namespace de Kubernetes |
| params.cronJobName | String | Si | Nombre del CronJob |
| params.clusterName | String | Si | Nombre del cluster EKS |

##### Informacion Recopilada

1. Descripcion del CronJob
2. YAML del CronJob
3. Eventos del namespace

##### Archivos Generados

- `CRONJOB_INFO_${cronJobName}-${namespace}.log`
- `EVENTS_${cronJobName}-${namespace}.log`

##### Ejemplo

```groovy
k8sFunctions.gatherCronJobDebugInfo(
    namespace: 'production',
    cronJobName: 'data-sync-job',
    clusterName: 'prod-cluster'
)
```

---

### Retry Mechanisms

#### retry

Ejecuta una operacion con reintentos y delay entre intentos.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| maxRetries | Integer | Si | Numero maximo de reintentos |
| retryDelay | Integer | Si | Tiempo de espera en segundos |
| closure | Closure | Si | Operacion a ejecutar |

##### Caracteristicas

- Valida endpoint de AWS EKS antes de cada intento
- Lanza la ultima excepcion si todos los reintentos fallan

##### Ejemplo

```groovy
k8sFunctions.retry(3, 10) {
    sh "kubectl get pods -n production"
}
```

---

#### retryWithDelay

Ejecuta una operacion con reintentos especificados.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| closure | Closure | Si | Operacion a ejecutar |
| retries | Integer | Si | Numero maximo de intentos |
| delaySeconds | Integer | Si | Tiempo de espera entre intentos |

##### Retorna

`Boolean` - `true` si la operacion fue exitosa, `false` si se agotaron los intentos.

##### Ejemplo

```groovy
if (k8sFunctions.retryWithDelay({ checkDeploymentExists('mi-api', 'prod') }, 5, 10)) {
    println "Deployment encontrado"
}
```

---

#### retryWithDeleteAndReapply

Ejecuta una operacion con reintentos, eliminando y reaplicando el manifiesto en caso de fallo.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| closure | Closure | Si | Operacion a ejecutar |
| deploymentFile | String | Si | Archivo de manifiesto |
| retries | Integer | Si | Numero maximo de intentos |
| delaySeconds | Integer | Si | Tiempo de espera entre intentos |

##### Retorna

`Boolean` - `true` si la operacion fue exitosa.

##### Ejemplo

```groovy
k8sFunctions.retryWithDeleteAndReapply(
    { applyManifest('./k8s/api.yaml') },
    './k8s/api.yaml',
    5,
    12
)
```

---

### Utility Functions

#### timeWait

Calcula el tiempo total de espera para un despliegue basado en parametros de readiness probes.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| readinessF | String/Integer | No | Umbral de fallos (default: 2) |
| readinessP | String/Integer | No | Periodo en segundos (default: 15) |
| readinessT | String/Integer | No | Timeout en segundos (default: 5) |
| readinessI | String/Integer | No | Delay inicial en segundos (default: 30) |

##### Formula

```
totalWaitTime = initialDelay + (failureThreshold + 1) * (periodSeconds + timeoutSeconds)
```

##### Retorna

`Integer` - Tiempo total en segundos.

##### Ejemplo

```groovy
def timeout = k8sFunctions.timeWait('3', '10', '5', '20')
println "Timeout calculado: ${timeout} segundos"
```

---

#### versionIsDeployedOnPre

Atajo de `versionIsDeployedOnEnvironment` con ambiente `pre`.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| anAppDeployName | String | Si | Nombre del deployment |
| aContainerVersion | String | Si | Version esperada |
| anAppNamespace | String | Si | Namespace |

##### Retorna

`Boolean` - `true` si el tag de la imagen desplegada coincide.

##### Ejemplo

```groovy
if (k8sFunctions.versionIsDeployedOnPre('mi-api', '1.2.0', 'pre')) {
    println "La version ya esta en pre"
}
```

---

#### versionIsDeployedOnProd

Atajo de `versionIsDeployedOnEnvironment` con ambiente `prod`.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| anAppDeployName | String | Si | Nombre del deployment |
| aContainerVersion | String | Si | Version esperada |

El namespace no es parametro. La llamada usa la variable `anAppNamespace` del binding del pipeline.

##### Retorna

`Boolean` - `true` si el tag de la imagen desplegada coincide.

##### Ejemplo

```groovy
anAppNamespace = 'prod'
if (k8sFunctions.versionIsDeployedOnProd('mi-api', '1.2.0')) {
    println "La version ya esta en prod"
}
```

---

#### versionIsDeployedOnEnvironment

Verifica si una version especifica esta desplegada en un ambiente.

##### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| anAppDeployName | String | Si | Nombre del deployment |
| aContainerVersion | String | Si | Version esperada |
| anAppNamespace | String | Si | Namespace |
| environment | String | Si | Ambiente (`sandbox`, `pre`, `prod`) |

Lee la imagen con `kubectl get deploy`. En `sandbox` la version es el ultimo segmento separado por `-`. En el resto de ambientes es el tag despues de `:`.

##### Retorna

`Boolean` - `true` si la version coincide.

##### Ejemplo

```groovy
if (k8sFunctions.versionIsDeployedOnEnvironment('mi-api', '1.0.0', 'prod', 'prod')) {
    println "Version correcta desplegada"
}
```

---

## Notas Importantes

### Prerequisitos

- AWS CLI configurado con credenciales validas
- kubectl instalado en el agente de Jenkins
- Helm instalado (para funciones de Helm)
- Acceso configurado a clusters EKS
- Credenciales de Nexus (para Helm charts)

### Variables de Entorno Globales

Las siguientes variables suelen ser configuradas a nivel de pipeline:

- `CLUSTER_NAME`: Nombre del cluster EKS
- `NAMESPACE`: Namespace por defecto
- `AWS_REGION`: Region de AWS
- `CONTAINER_IMAGE_TAG`: Tag de la imagen por defecto
- `FORCE_K8S_DEPLOY`: Activa modo forzado de despliegue
- `K8S_ROLLBACK`: Controla el rollback ante un fallo de rollout. Por defecto se hace rollback; `"false"` deja la version fallida

### Readiness Probes

Las funciones calculan timeouts inteligentes basados en readiness probes:

- `READINESS_FAILURE_TH`: Umbral de fallos consecutivos
- `READINESS_PERIOD_SEC`: Intervalo entre checks
- `READINESS_TIMEOUT_SEC`: Timeout por check
- `READINESS_INITIAL_DELAY`: Delay antes del primer check

### Troubleshooting Automatico

En caso de fallos de despliegue:

1. Se obtienen logs del pod fallido
2. Se recopila informacion completa del cluster
3. Se realiza rollback automatico, salvo que `K8S_ROLLBACK` sea `"false"`
4. Se archivan logs como artefactos de Jenkins

### Rollback ante fallo de rollout

Por defecto, si el rollout no queda ready, `deployUnifiedManifest` vuelve a la version anterior.

Cuando `env.K8S_ROLLBACK = "false"`:

- No se ejecuta el rollback
- Se deja desplegada la version que fallo
- El pipeline igual falla y se recopila la informacion de debug

### Modo Forzado

Cuando `env.FORCE_K8S_DEPLOY = "true"`:

- Elimina recursos existentes antes de reaplicar
- util para resolver conflictos de recursos
- Usa `retryWithDeleteAndReapply` en lugar de `retryWithDelay`

### Manejo de ReplicaSets

Las funciones validan y limpian ReplicaSets:

- Solo un ReplicaSet debe estar activo
- Si hay multiples, se elimina el mas antiguo
- Previene problemas de sincronizacion

---

## Ejemplo Completo de Pipeline

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        CLUSTER_NAME = 'production-cluster'
        NAMESPACE = 'production'
        AWS_REGION = 'us-east-1'
        CONTAINER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        // Readiness probe configuration
        READINESS_FAILURE_TH = '3'
        READINESS_PERIOD_SEC = '10'
        READINESS_TIMEOUT_SEC = '5'
        READINESS_INITIAL_DELAY = '30'
    }

    stages {
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    try {
                        k8sFunctions.deployUnifiedManifest(
                            clusterName: env.CLUSTER_NAME,
                            k8sDeployPath: './k8s',
                            imageName: 'mi-api',
                            nameSpace: env.NAMESPACE,
                            awsRegion: env.AWS_REGION,
                            imageTag: env.CONTAINER_IMAGE_TAG,
                            retries: 5,
                            delay: 12
                        )
                    } catch (Exception e) {
                        echo "Error en despliegue: ${env.MENSAJE}"
                        throw e
                    }
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    def currentVersion = k8sFunctions.getVersionDeploy('mi-api', env.NAMESPACE)
                    if (currentVersion == env.CONTAINER_IMAGE_TAG) {
                        echo "Despliegue verificado: version ${currentVersion}"
                    } else {
                        error "Version incorrecta: ${currentVersion}"
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                // Los logs ya fueron recopilados automaticamente por gatherK8sDebugInfo
                echo "Revise los artefactos del build para informacion de debug"
            }
        }
    }
}
```

---

## Pipeline con CronJob

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        CLUSTER_NAME = 'production-cluster'
        NAMESPACE = 'batch-jobs'
        AWS_REGION = 'us-east-1'
        CONTAINER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        CRONJOB_SCHEDULE = '0 2 * * *'  // Esta variable activa el modo CronJob
    }

    stages {
        stage('Deploy CronJob') {
            steps {
                script {
                    k8sFunctions.deployOrchestrator(
                        clusterName: env.CLUSTER_NAME,
                        k8sDeployPath: './k8s',
                        resourceName: 'data-sync-job',
                        nameSpace: env.NAMESPACE,
                        awsRegion: env.AWS_REGION,
                        imageTag: env.CONTAINER_IMAGE_TAG
                    )
                }
            }
        }
    }
}
```

---

## Pipeline con Helm

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        CREDENTIAL_NEXUS = 'nexus-credentials'
        HELM_CHART_REGISTRY_URL = 'https://nexus.example.com/repository/helm-charts'
        HELM_CHART_REGISTRY_FILENAME = 'my-chart-1.0.0.tgz'
        HELM_CHART_DEPLOY_NAME = 'my-app'
        NAMESPACE = 'production'
        ENV_NAME = 'prod'
        DOCKER_IMAGE_SINGLE_NAME = 'my-api'
        DOCKER_GCP_IMAGE_NAME = 'gcr.io/my-project/my-api'
        DOCKER_IMAGE_TAG = "${env.BUILD_NUMBER}"
        MICROSERVICE_NAME = 'my-api'
    }

    stages {
        stage('Deploy with Helm') {
            steps {
                script {
                    k8sFunctions.helmInstall('true', 'false')
                }
            }
        }

        stage('List Helm Releases') {
            steps {
                script {
                    k8sFunctions.helmList()
                }
            }
        }
    }
}
```

**Tags:** `#kubernetes`, `#k8s`, `#eks`, `#helm`, `#deployment`, `#cronjob`, `#aws`, `#jenkins`, `#pipeline`, `#troubleshooting`