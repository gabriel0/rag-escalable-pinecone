# kustomizeBuild

Biblioteca de funciones para generar y personalizar manifiestos de Kubernetes utilizando Kustomize.

## Descripcion

Este conjunto de funciones proporciona una solucion completa para la generacion dinamica de manifiestos de Kubernetes mediante Kustomize, incluyendo configuracion de recursos, parches, secretos, ConfigMaps, HPA, Ingress, CronJobs, y mas. Automatiza el proceso de construccion de manifiestos personalizados basados en variables de entorno.

---

## Funciones Principales

### kustomizeProcess

Ejecuta el proceso completo de Kustomize para generar y personalizar los manifiestos de Kubernetes.

#### Descripcion

Funcion orquestadora que ejecuta condicionalmente todas las operaciones de Kustomize basandose en la presencia de variables de entorno especificas.

#### Proceso de Ejecucion

1. **Configuracion de PVC** (si `CLAIM_NAME` esta definido)
2. **Configuracion de KeyStore** (si `KEYSTORE_NAME` esta definido)
3. **Configuracion de Role/ServiceAccount** (si `SERVICE_ARN_ROLE` esta definido)
4. **Configuracion de Ingress AWS** (si `ROUTE_PATH` esta definido)
5. **Configuracion de Target Group Binding** (si `TG_ARN` esta definido)
6. **Configuracion de HPA** (si `HPA_TYPE` esta definido)
7. **Configuracion de Secret Manager Store** (si `SECRET_PROVIDER_CLASS` esta definido)
8. **Configuracion de External Secrets** (si `EXTERNAL_SECRET` esta definido)
9. **Configuracion del path de Kustomize**
10. **Creacion de ConfigMap** (desde `configuraciones.properties`)
11. **Creacion de Secret** (desde `secrets.properties`)
12. **Aplicacion de parches unificados** (Deployment o CronJob)
13. **Aplicacion de parche de imagen**
14. **Construccion final del manifiesto**
15. **Aplicacion de valores personalizados**

#### Ejemplo

```groovy
stage('Generate Manifests') {
    steps {
        script {
            kustomizeBuild.kustomizeProcess()
        }
    }
}
```

---

## Funciones de Configuracion

### kustomizePathSet

Establece la ruta de trabajo de Kustomize.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| appName | String | Si | Nombre de la aplicacion |
| environment | String | Si | Nombre del entorno (dev, pre, prod) |

#### Resultado

Establece `env.kustomizePath = "Gitops/${appName}/${environment}"`

#### Ejemplo

```groovy
kustomizeBuild.kustomizePathSet('mi-api', 'production')
// env.kustomizePath = "Gitops/mi-api/production"
```

---

### kustomizeBuild

Realiza la construccion final del manifiesto de Kubernetes utilizando Kustomize.

#### Variables de Entorno Requeridas

- `NAMESPACE`: Namespace donde se desplegara la aplicacion
- `IMAGE_NAME`: Nombre de la imagen del contenedor

#### Proceso

1. Establece el namespace en el manifiesto
2. Crea el directorio de salida
3. Genera el archivo de manifiesto final

#### Archivo Generado

`${kustomizePath}/${IMAGE_NAME}-manifiesto.yaml`

#### Ejemplo

```groovy
env.NAMESPACE = 'production'
env.IMAGE_NAME = 'mi-api'
kustomizeBuild.kustomizeBuild()
// Genera: Gitops/mi-api/production/mi-api-manifiesto.yaml
```

---

## Funciones de Parches

### kustomizePatchingUnified

Añade un parche unificado para Deployment, incluyendo sondas de liveness, readiness y startup.

#### Variables de Entorno Requeridas

- `REPLICAS`: Numero de replicas
- `CONTAINER_PORT`: Puerto del contenedor
- `LIMITS_CPU`: Limite de CPU (ej: "500m")
- `LIMITS_MEMORY`: Limite de memoria (ej: "512Mi")
- `REQUEST_CPU`: Solicitud de CPU
- `REQUEST_MEMORY`: Solicitud de memoria
- `LIVENESS_INITIAL_DELAY`: Delay inicial para liveness probe
- `LIVENESS_PERIOD_SEC`: Periodo de liveness probe
- `LIVENESS_TIMEOUT_SEC`: Timeout de liveness probe
- `LIVENESS_SUCCESS_TH`: Umbral de exito
- `LIVENESS_FAILURE_TH`: Umbral de fallo
- `READINESS_INITIAL_DELAY`: Delay inicial para readiness probe
- `READINESS_PERIOD_SEC`: Periodo de readiness probe
- `READINESS_TIMEOUT_SEC`: Timeout de readiness probe
- `READINESS_SUCCESS_TH`: Umbral de exito
- `READINESS_FAILURE_TH`: Umbral de fallo

#### Variables Opcionales para Probes

- `LIVENESS_TYPE`: "TCP", "HTTP", o "HTTPS"
- `LIVENESS_PATH`: Ruta para HTTP/HTTPS probe
- `READINESS_TYPE`: "TCP", "HTTP", o "HTTPS"
- `READINESS_PATH`: Ruta para HTTP/HTTPS probe
- `STARTUP_TYPE`: "TCP", "HTTP", o "HTTPS"
- `STARTUP_PATH`: Ruta para HTTP/HTTPS probe
- `STARTUP_*`: Parametros de startup probe

#### Variable Opcional para Estrategia de Despliegue

- `ROLLING_UPDATE_MAX_PERCENT`: Porcentaje a utilizar tanto para `maxSurge` como para `maxUnavailable` de la estrategia `RollingUpdate` del Deployment. Valores permitidos: `"25%"`, `"50%"`, `"75%"`, `"100%"`. Si no se define, se utiliza `"25%"` por defecto. Si se define con un valor no permitido, la funcion lanza un `RuntimeException`.

##### Que significan `maxSurge` y `maxUnavailable`

Kubernetes actualiza un Deployment reemplazando gradualmente los Pods de la version vieja por Pods de la version nueva (rolling update). Estos dos campos controlan que tan agresivo o conservador es ese reemplazo, y se calculan como porcentaje sobre `REPLICAS`:

- **`maxSurge`**: cuantos Pods **de mas** (por encima de `REPLICAS`) puede crear Kubernetes temporalmente mientras dura la actualizacion. Un valor mayor acelera el despliegue porque los Pods nuevos se levantan antes de bajar los viejos, pero consume mas recursos del cluster (CPU/memoria/IPs) durante la transicion.
- **`maxUnavailable`**: cuantos Pods de la version vieja puede tumbar Kubernetes **antes** de que el reemplazo equivalente este listo (`Ready`). Un valor mayor acelera el despliegue porque se apagan mas Pods viejos en paralelo, pero reduce la capacidad/redundancia disponible para atender trafico mientras el rollout esta en curso.

##### Como afecta esto a un despliegue en la practica

Ambos porcentajes se redondean hacia arriba y se aplican sobre `REPLICAS`. Por ejemplo, con `REPLICAS=4`:

| `ROLLING_UPDATE_MAX_PERCENT` | maxSurge (Pods extra) | maxUnavailable (Pods caidos) | Efecto |
| --- | --- | --- | --- |
| `25%` (default) | 1 | 1 | Rollout mas lento y conservador: nunca hay mas de 5 Pods corriendo ni menos de 3 disponibles. Ideal para servicios criticos o con recursos limitados en el cluster. |
| `50%` | 2 | 2 | Rollout mas rapido, con mayor consumo temporal de recursos y mayor reduccion de capacidad durante la actualizacion. |
| `75%` | 3 | 3 | Rollout aun mas agresivo; solo queda garantizado 1 Pod disponible en el peor caso. |
| `100%` | 4 | 4 | El Deployment puede llegar a duplicar temporalmente la cantidad de Pods (hasta 8) y, en el peor caso, quedarse sin ningun Pod de la version vieja disponible antes de que los nuevos esten `Ready`. Recomendado solo si el cluster tiene capacidad de sobra y el servicio tolera una ventana sin redundancia. |

En resumen: subir `ROLLING_UPDATE_MAX_PERCENT` acelera los despliegues a costa de mayor consumo de recursos (`maxSurge`) y/o menor disponibilidad momentanea (`maxUnavailable`). Dejarlo en el valor por defecto (`25%`) prioriza estabilidad y bajo impacto sobre el cluster durante el rollout.

#### Ejemplo

```groovy
env.REPLICAS = '3'
env.CONTAINER_PORT = '8080'
env.LIMITS_CPU = '1000m'
env.LIMITS_MEMORY = '1Gi'
env.REQUEST_CPU = '500m'
env.REQUEST_MEMORY = '512Mi'
env.LIVENESS_TYPE = 'HTTP'
env.LIVENESS_PATH = '/health'
env.LIVENESS_INITIAL_DELAY = '30'
env.LIVENESS_PERIOD_SEC = '10'
env.ROLLING_UPDATE_MAX_PERCENT = '50%'
// ... otros parametros
kustomizeBuild.kustomizePatchingUnified()
```

---

### kustomizePatchingCronJob

Crea y aplica un parche para un recurso CronJob.

#### Variables de Entorno Requeridas

- `CRONJOB_SCHEDULE`: Expresion cron (ej: "0 2 * * *")
- `IMAGE_NAME`: Nombre de la imagen
- `APP_VERSION`: Version de la aplicacion
- `LIMITS_CPU`: Limite de CPU
- `LIMITS_MEMORY`: Limite de memoria
- `REQUEST_CPU`: Solicitud de CPU
- `REQUEST_MEMORY`: Solicitud de memoria
- `SERVICE_ACCOUNT`: Cuenta de servicio

#### Variables Opcionales

- `SUSPEND_CRONJOB`: "true" o "false" (default: "false")

#### Caracteristicas

- Valida la expresion cron
- Configura timezone: "America/Argentina/Buenos_Aires"
- Monta ConfigMaps y Secrets automaticamente si existen

#### Ejemplo

```groovy
env.CRONJOB_SCHEDULE = '0 2 * * *'
env.SUSPEND_CRONJOB = 'false'
env.LIMITS_CPU = '500m'
env.LIMITS_MEMORY = '512Mi'
env.REQUEST_CPU = '250m'
env.REQUEST_MEMORY = '256Mi'
env.SERVICE_ACCOUNT = 'cronjob-sa'
kustomizeBuild.kustomizePatchingCronJob()
```

---

### kustomizePatchImage

Añade un parche para la imagen del contenedor.

#### Variables de Entorno Requeridas

- `ECR_REGISTRY`: Registro de contenedores
- `ECR_REPOSITORY`: Repositorio de contenedores
- `IMAGE_NAME`: Nombre de la imagen
- `APP_VERSION`: Version de la aplicacion

#### Comportamiento

- Si `CRONJOB_SCHEDULE` esta definido: parche para CronJob
- Caso contrario: parche para Deployment

#### Ejemplo

```groovy
env.ECR_REGISTRY = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
env.ECR_REPOSITORY = 'mi-repositorio'
env.IMAGE_NAME = 'mi-api'
env.APP_VERSION = '1.0.0'
kustomizeBuild.kustomizePatchImage()
// Imagen resultante: 123456789012.dkr.ecr.us-east-1.amazonaws.com/mi-repositorio/mi-api:1.0.0
```

---

## Funciones de Recursos de Kubernetes

### kustomizeIngressAws

Genera una configuracion de Ingress para AWS ALB.

#### Tipos de Ingress Soportados

1. **Target** (`INGRESS_TYPE="target"`): ALB independiente por servicio
2. **Group** (`INGRESS_TYPE="group"`): ALB compartido entre servicios

#### Variables Requeridas (Ambos Tipos)

- `IMAGE_NAME`: Nombre de la imagen
- `ROUTE_PATH`: Ruta del servicio
- `CERTIFICATE_ARN`: ARN del certificado SSL
- `CONTAINER_PORT`: Puerto del contenedor

#### Variables Adicionales para Type="group"

- `APP_NAME`: Nombre de la aplicacion (para grupo de Ingress)
- `LIVENESS_PERIOD_SEC`: Intervalo de healthcheck
- `INGRESS_HOSTNAME`: Hostname del Ingress

#### Variables Opcionales

- `ROUTE_PATH_TYPE`: Tipo de coincidencia de la ruta (`Prefix`, `Exact`, `ImplementationSpecific`). Por defecto `Prefix`.
- `ALB_PRIORITY`: Prioridad de la regla ALB
- `ALB_GROUP_ORDER`: Orden del grupo ALB
- `LIVENESS_PATH`: Ruta personalizada para healthcheck
- `INGRESS_LABEL`: "false" para desactivar labels adicionales

#### Ejemplo Type="target"

```groovy
env.INGRESS_TYPE = 'target'
env.IMAGE_NAME = 'mi-api'
env.ROUTE_PATH = '/api/*/ofertador/generacion'
env.ROUTE_PATH_TYPE = 'ImplementationSpecific'
env.CERTIFICATE_ARN = 'arn:aws:acm:us-east-1:123456789012:certificate/...'
env.CONTAINER_PORT = '8080'
kustomizeBuild.kustomizeIngressAws()
```

#### Ejemplo Type="group"

```groovy
env.INGRESS_TYPE = 'group'
env.IMAGE_NAME = 'mi-api'
env.APP_NAME = 'mi-aplicacion'
env.ROUTE_PATH = '/api/*'
env.CERTIFICATE_ARN = 'arn:aws:acm:us-east-1:123456789012:certificate/...'
env.CONTAINER_PORT = '8080'
env.LIVENESS_PERIOD_SEC = '30'
env.INGRESS_HOSTNAME = 'api.example.com'
env.ALB_PRIORITY = '10'
kustomizeBuild.kustomizeIngressAws()
```

---

### kustomizeTargetGroupBinding

Crea un manifiesto de TargetGroupBinding para vincular un Service con un Target Group de AWS.

#### Variables de Entorno Requeridas

- `IMAGE_NAME`: Nombre base
- `TG_ARN`: ARN del Target Group de AWS existente
- `CONTAINER_PORT`: Puerto del Service

#### Descripcion

TargetGroupBinding es un CRD del AWS Load Balancer Controller que permite vincular un Service de Kubernetes con un Target Group de AWS existente.

#### Ejemplo

```groovy
env.IMAGE_NAME = 'mi-api'
env.TG_ARN = 'arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/...'
env.CONTAINER_PORT = '8080'
kustomizeBuild.kustomizeTargetGroupBinding()
```

---

### kustomizeHpa

Genera una configuracion de Horizontal Pod Autoscaler (HPA).

#### Variables de Entorno Requeridas

- `IMAGE_NAME`: Nombre de la imagen
- `HPA_MIN_REPL`: Replicas minimas
- `HPA_MAX_REPL`: Replicas maximas
- `HPA_TYPE`: "cpu", "memory", o "both"

#### Variables Condicionales

- `HPA_AVERAGE_CPU_UTILIZATION`: Requerido si HPA_TYPE incluye CPU
- `HPA_AVERAGE_MEM_UTILIZATION`: Requerido si HPA_TYPE incluye memoria

#### Comportamiento de Escalado

- **Scale Up**: Estabilizacion de 120s, politica maxima, hasta HPA_MAX_REPL pods cada 300s
- **Scale Down**: Estabilizacion de 300s, politica minima, hasta HPA_MIN_REPL pods cada 120s

#### Ejemplo

```groovy
env.IMAGE_NAME = 'mi-api'
env.HPA_MIN_REPL = '2'
env.HPA_MAX_REPL = '10'
env.HPA_TYPE = 'both'
env.HPA_AVERAGE_CPU_UTILIZATION = '70'
env.HPA_AVERAGE_MEM_UTILIZATION = '80'
kustomizeBuild.kustomizeHpa()
```

---

## Funciones de Volumenes y Secretos

### kustomizePatchPvc

Añade un parche para un Persistent Volume Claim (PVC).

#### Variables de Entorno Requeridas

- `IMAGE_NAME`: Nombre de la imagen
- `CLAIM_NAME`: Nombre del PVC existente
- `MOUNT_PATH`: Ruta de montaje en el contenedor

#### Ejemplo

```groovy
env.IMAGE_NAME = 'mi-api'
env.CLAIM_NAME = 'mi-pvc-data'
env.MOUNT_PATH = '/data'
kustomizeBuild.kustomizePatchPvc()
```

---

### kustomizePatchKeyStore

Añade un parche para un KeyStore montado desde un Secret.

#### Variables de Entorno Requeridas

- `KEYSTORE_NAME`: Nombre del KeyStore (ej: "keystore.jks")
- `KEYSTORE_SECRET_NAME`: Nombre del Secret que contiene el KeyStore
- `KEYSTORE_MOUNT_PATH`: Ruta de montaje

#### Ejemplo

```groovy
env.KEYSTORE_NAME = 'keystore.jks'
env.KEYSTORE_SECRET_NAME = 'mi-keystore-secret'
env.KEYSTORE_MOUNT_PATH = '/app/certs'
kustomizeBuild.kustomizePatchKeyStore()
// Resultado: Monta en /app/certs/keystore.jks
```

---

### kustomizePatchSecretManagerStore

Añade un parche para AWS Secrets Store CSI Driver.

#### Variables de Entorno Requeridas

- `SECRET_VOLUME_NAME`: Nombre del volumen
- `SECRET_PROVIDER_CLASS`: Nombre del SecretProviderClass
- `SECRET_MOUNT_PATH`: Ruta de montaje

#### Descripcion

Configura el CSI Driver de Secrets Store para montar secretos de AWS Secrets Manager como volumenes.

#### Ejemplo

```groovy
env.SECRET_VOLUME_NAME = 'secrets-store'
env.SECRET_PROVIDER_CLASS = 'aws-secrets'
env.SECRET_MOUNT_PATH = '/mnt/secrets-store'
kustomizeBuild.kustomizePatchSecretManagerStore()
```

---

## Funciones de ConfigMaps y Secrets

### kustomizeConfigMap

Crea un ConfigMap desde el archivo `configuraciones.properties`.

#### Variables de Entorno Requeridas

- `NAMESPACE`: Namespace donde se creara el ConfigMap
- `IMAGE_NAME`: Nombre del ConfigMap

#### Archivo Esperado

`configuraciones.properties` en el directorio actual

#### Comportamiento

- Si el archivo existe: crea ConfigMap con nombre `${IMAGE_NAME}`
- Si no existe: omite la creacion
- Establece variable `HAS_CONFIGMAP` para uso posterior

#### Ejemplo de archivo configuraciones.properties

```properties
DATABASE_HOST=db.example.com
DATABASE_PORT=5432
LOG_LEVEL=INFO
```

#### Ejemplo

```groovy
env.NAMESPACE = 'production'
env.IMAGE_NAME = 'mi-api'
kustomizeBuild.kustomizeConfigMap()
```

---

### kustomizeSecret

Crea un Secret desde el archivo `secrets.properties`.

#### Variables de Entorno Requeridas

- `NAMESPACE`: Namespace donde se creara el Secret
- `IMAGE_NAME`: Nombre del Secret

#### Archivo Esperado

`secrets.properties` en el directorio actual

#### Comportamiento

- Si el archivo existe: crea Secret con nombre `${IMAGE_NAME}`
- Si no existe: omite la creacion
- Establece variable `HAS_SECRET` para uso posterior

#### Ejemplo de archivo secrets.properties

```properties
DATABASE_PASSWORD=supersecret
API_KEY=123456789
JWT_SECRET=verysecretkey
```

#### Ejemplo

```groovy
env.NAMESPACE = 'production'
env.IMAGE_NAME = 'mi-api'
kustomizeBuild.kustomizeSecret()
```

---

## Funciones de External Secrets

### kustomizeSecretStoreResource

Crea un recurso SecretStore para External Secrets Operator.

#### Variables de Entorno Requeridas

- `APP_NAME`: Nombre de la aplicacion
- `NAMESPACE`: Namespace
- `AWS_REGION`: Region de AWS
- `SERVICE_ACCOUNT`: ServiceAccount con IRSA configurado

#### Descripcion

Genera un SecretStore que se conecta a AWS Secrets Manager usando IRSA (IAM Roles for Service Accounts).

#### Ejemplo

```groovy
env.APP_NAME = 'mi-aplicacion'
env.NAMESPACE = 'production'
env.AWS_REGION = 'us-east-1'
env.SERVICE_ACCOUNT = 'external-secrets-sa'
kustomizeBuild.kustomizeSecretStoreResource()
// Crea: mi-aplicacion-secret-store
```

---

### kustomizeExternalSecretResource

Crea un recurso ExternalSecret para sincronizar secretos de AWS Secrets Manager.

#### Variables de Entorno Requeridas

- `APP_NAME`: Nombre de la aplicacion
- `NAMESPACE`: Namespace
- `SECRET_KEYS`: Nombres de secretos en AWS, separados por comas

#### Variables Opcionales

- `EXTERNAL_SECRET_REFRESH_INTERVAL`: Intervalo de actualizacion (default: "1h")

#### Comportamiento

- Extrae multiples secretos de AWS Secrets Manager
- Crea un Secret de Kubernetes con todas las claves
- Establece `env.EXTERNAL_SECRET_REF` para referencias posteriores

#### Ejemplo

```groovy
env.APP_NAME = 'mi-aplicacion'
env.NAMESPACE = 'production'
env.SECRET_KEYS = 'database-credentials, api-keys, jwt-secret'
env.EXTERNAL_SECRET_REFRESH_INTERVAL = '30m'
kustomizeBuild.kustomizeExternalSecretResource()
// Crea ExternalSecret que sincroniza 3 secretos de AWS
```

---

## Funciones de RBAC

### kustomizeRole

Añade un parche para Role con permisos basicos.

#### Variables de Entorno Requeridas

- `APP_NAME`: Nombre de la aplicacion

#### Permisos Configurados

- `services`: get, list
- `secrets`: get
- `configmaps`: get
- `endpoints` o `endpointslices`: get, list (segun version de Kubernetes)
- `pods`: get, list

#### Discovery de endpoints segun version de Kubernetes

Desde Kubernetes 1.33, el recurso `Endpoints` (core/v1) esta deprecado. La libreria selecciona automaticamente:

- **< 1.33**: RBAC con `endpoints` en apiGroup `""`
- **>= 1.33**: RBAC con `endpointslices` en apiGroup `discovery.k8s.io`

La version se resuelve en este orden:

1. `K8S_VERSION`, `EKS_VERSION`, `KUBERNETES_VERSION` o `CLUSTER_VERSION`
2. `aws eks describe-cluster` usando `CLUSTER_NAME` y `AWS_REGION`
3. Si no hay version, se mantiene `endpoints` (compatibilidad con clusters antiguos)

Cuando `SERVICE_ARN_ROLE` no esta definido, el Role base de `base/rbac.yaml` se parchea antes del build si la version es >= 1.33.

#### Funciones Relacionadas

Automaticamente invoca:
- `kustomizeServiceAccount()`
- `kustomizeRoleBinding()`
- `kustomizeAddSa()`

#### Ejemplo

```groovy
env.APP_NAME = 'mi-aplicacion'
env.SERVICE_ARN_ROLE = 'arn:aws:iam::123456789012:role/mi-rol'
env.SERVICE_ACCOUNT = 'mi-sa'
env.NAMESPACE = 'production'
kustomizeBuild.kustomizeRole()
```

---

### kustomizeServiceAccount

Crea un ServiceAccount, opcionalmente con anotacion para IRSA.

#### Variables de Entorno Requeridas

- `SERVICE_ACCOUNT`: Nombre del ServiceAccount

#### Variables Opcionales

- `SERVICE_ARN_ROLE`: ARN del rol IAM (para IRSA)

#### Ejemplo

```groovy
env.SERVICE_ACCOUNT = 'mi-service-account'
env.SERVICE_ARN_ROLE = 'arn:aws:iam::123456789012:role/eks-pod-role'
kustomizeBuild.kustomizeServiceAccount()
```

---

### kustomizeRoleBinding

Crea un RoleBinding que asocia Role con ServiceAccount.

#### Variables de Entorno Requeridas

- `APP_NAME`: Nombre de la aplicacion
- `SERVICE_ACCOUNT`: Nombre del ServiceAccount
- `NAMESPACE`: Namespace

#### Ejemplo

```groovy
env.APP_NAME = 'mi-aplicacion'
env.SERVICE_ACCOUNT = 'mi-sa'
env.NAMESPACE = 'production'
kustomizeBuild.kustomizeRoleBinding()
```

---

### kustomizeAddSa

Añade configuracion de ServiceAccount al Deployment.

#### Variables de Entorno Requeridas

- `SERVICE_ACCOUNT`: Nombre del ServiceAccount

#### Configuracion Aplicada

- `automountServiceAccountToken: true`
- `serviceAccountName: ${SERVICE_ACCOUNT}`

---

## Funciones Auxiliares

### resolveRollingUpdateMaxPercent

Resuelve y valida el porcentaje a utilizar para `maxSurge`/`maxUnavailable` de la estrategia `RollingUpdate`.

#### Comportamiento

- Si `ROLLING_UPDATE_MAX_PERCENT` no esta definida (o vacia): retorna `"25%"` (valor por defecto).
- Si esta definida: valida que sea uno de `"25%"`, `"50%"`, `"75%"`, `"100%"`; si no lo es, lanza `RuntimeException`.

#### Ejemplo

```groovy
env.ROLLING_UPDATE_MAX_PERCENT = '50%'
def porcentaje = kustomizeBuild.resolveRollingUpdateMaxPercent()
// porcentaje == '50%'
```

---

### nullOrEmpty

Valida que las variables de entorno especificadas no sean nulas ni vacias.

#### Parametros

Nombres de variables de entorno a validar (varargs)

#### Comportamiento

Lanza `RuntimeException` si alguna variable es nula o vacia.

#### Ejemplo

```groovy
kustomizeBuild.nullOrEmpty("APP_NAME", "NAMESPACE", "IMAGE_NAME")
// Lanza excepcion si alguna esta vacia o no definida
```

---

### kustomizeCustomValues

Reemplaza valores de marcador de posicion en el manifiesto generado.

#### Parametros

| Nombre | Tipo | Descripcion |
|--------|------|-------------|
| dcfile | String | Nombre del archivo de manifiesto |

#### Reemplazos Realizados

- `SERVICE_ACCOUNT` → `${env.SERVICE_ACCOUNT}`
- `NAMESPACE` → `${env.NAMESPACE}`
- `APP_NAME` → `${env.APP_NAME}`
- `IMAGE_NAME` → `${env.IMAGE_NAME}`
- `PUERTOAPP` → `${env.CONTAINER_PORT}`
- `APP_VERSION` → `${env.APP_VERSION}`
- `INGRESS_HOSTNAME` → `${env.INGRESS_HOSTNAME}`

#### Ejemplo

```groovy
kustomizeBuild.kustomizeCustomValues("mi-api-manifiesto.yaml")
```

---

## Estructura de Archivos

### Archivos Base Requeridos

Deben existir en `../../base/`:
- `deployment.yaml`: Template de Deployment
- `service.yaml`: Template de Service
- `cronjob.yaml`: Template de CronJob (si se usa)
- `kustomization.yaml`: Kustomization base

### Archivos de Configuracion Opcionales

- `configuraciones.properties`: Para ConfigMap
- `secrets.properties`: Para Secret

### Archivos Generados

Durante el proceso se generan:
- `kustomization.yaml`: En el overlay
- `patch-deployment.yaml` o `patch-cronjob.yaml`
- `image.yaml`
- `configmap.yaml` (si aplica)
- `secret.yaml` (si aplica)
- `hpa.yaml` (si aplica)
- `ingress-alb.yaml` (si aplica)
- Y otros segun configuracion

---

## Ejemplo Completo de Pipeline

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        // Configuracion basica
        APP_NAME = 'mi-aplicacion'
        IMAGE_NAME = 'mi-api'
        ENVIRONMENT = 'production'
        NAMESPACE = 'production'

        // Imagen
        ECR_REGISTRY = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
        ECR_REPOSITORY = 'mi-repositorio'
        APP_VERSION = "${env.BUILD_NUMBER}"

        // Deployment
        REPLICAS = '3'
        CONTAINER_PORT = '8080'

        // Recursos
        LIMITS_CPU = '1000m'
        LIMITS_MEMORY = '1Gi'
        REQUEST_CPU = '500m'
        REQUEST_MEMORY = '512Mi'

        // Liveness Probe
        LIVENESS_TYPE = 'HTTP'
        LIVENESS_PATH = '/health'
        LIVENESS_INITIAL_DELAY = '30'
        LIVENESS_PERIOD_SEC = '10'
        LIVENESS_TIMEOUT_SEC = '5'
        LIVENESS_SUCCESS_TH = '1'
        LIVENESS_FAILURE_TH = '3'

        // Readiness Probe
        READINESS_TYPE = 'HTTP'
        READINESS_PATH = '/ready'
        READINESS_INITIAL_DELAY = '10'
        READINESS_PERIOD_SEC = '10'
        READINESS_TIMEOUT_SEC = '5'
        READINESS_SUCCESS_TH = '1'
        READINESS_FAILURE_TH = '3'

        // Ingress
        INGRESS_TYPE = 'group'
        ROUTE_PATH = '/api/*'
        CERTIFICATE_ARN = 'arn:aws:acm:us-east-1:123456789012:certificate/...'
        INGRESS_HOSTNAME = 'api.example.com'
        ALB_PRIORITY = '10'

        // HPA
        HPA_TYPE = 'both'
        HPA_MIN_REPL = '2'
        HPA_MAX_REPL = '10'
        HPA_AVERAGE_CPU_UTILIZATION = '70'
        HPA_AVERAGE_MEM_UTILIZATION = '80'

        // RBAC
        SERVICE_ACCOUNT = 'mi-api-sa'
        SERVICE_ARN_ROLE = 'arn:aws:iam::123456789012:role/eks-mi-api-role'
        AWS_REGION = 'us-east-1'
    }

    stages {
        stage('Prepare Configuration') {
            steps {
                script {
                    // Crear archivos de configuracion
                    writeFile file: 'configuraciones.properties', text: '''
DATABASE_HOST=db.production.example.com
DATABASE_PORT=5432
LOG_LEVEL=INFO
CACHE_ENABLED=true
                    '''.trim()

                    writeFile file: 'secrets.properties', text: '''
DATABASE_PASSWORD=encrypted_password
API_KEY=secret_key_here
JWT_SECRET=jwt_secret_key
                    '''.trim()
                }
            }
        }

        stage('Generate Kubernetes Manifests') {
            steps {
                script {
                    kustomizeBuild.kustomizeProcess()
                }
            }
        }

        stage('Verify Manifests') {
            steps {
                script {
                    sh "cat Gitops/${env.APP_NAME}/${env.ENVIRONMENT}/${env.IMAGE_NAME}-manifiesto.yaml"
                }
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: "Gitops/**/*.yaml", allowEmptyArchive: false
        }
        failure {
            echo "Error en generacion de manifiestos: ${env.MENSAJE}"
        }
    }
}
```

---

## Ejemplo de Pipeline con CronJob

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        APP_NAME = 'data-processor'
        IMAGE_NAME = 'data-processor-job'
        ENVIRONMENT = 'production'
        NAMESPACE = 'batch-jobs'

        ECR_REGISTRY = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
        ECR_REPOSITORY = 'batch-jobs'
        APP_VERSION = "${env.BUILD_NUMBER}"

        // CronJob especifico
        CRONJOB_SCHEDULE = '0 2 * * *'
        SUSPEND_CRONJOB = 'false'

        LIMITS_CPU = '2000m'
        LIMITS_MEMORY = '2Gi'
        REQUEST_CPU = '1000m'
        REQUEST_MEMORY = '1Gi'

        SERVICE_ACCOUNT = 'cronjob-processor-sa'
        SERVICE_ARN_ROLE = 'arn:aws:iam::123456789012:role/eks-cronjob-role'
        AWS_REGION = 'us-east-1'
    }

    stages {
        stage('Generate CronJob Manifests') {
            steps {
                script {
                    kustomizeBuild.kustomizeProcess()
                }
            }
        }
    }
}
```

---

## Notas Importantes

### Prerequisitos

- Kustomize instalado en el agente de Jenkins
- kubectl instalado (para generacion de ConfigMaps y Secrets)
- dos2unix instalado (para archivos de configuracion)
- Estructura de directorios Gitops configurada

### Estructura de Directorios Esperada

```
.
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── cronjob.yaml
│   └── kustomization.yaml
└── Gitops/
    └── ${APP_NAME}/
        └── ${ENVIRONMENT}/
            └── ${IMAGE_NAME}-manifiesto.yaml (generado)
```

### Variables de Entorno Comunes

#### Siempre Requeridas
- `APP_NAME`: Nombre de la aplicacion
- `IMAGE_NAME`: Nombre de la imagen
- `ENVIRONMENT`: Entorno (dev, pre, prod)
- `NAMESPACE`: Namespace de Kubernetes
- `ECR_REGISTRY`, `ECR_REPOSITORY`, `APP_VERSION`: Para imagen
- `CONTAINER_PORT`: Puerto del contenedor

#### Para Deployments
- `REPLICAS`: Numero de replicas
- `LIMITS_CPU`, `LIMITS_MEMORY`: Limites de recursos
- `REQUEST_CPU`, `REQUEST_MEMORY`: Solicitudes de recursos
- Parametros de probes (liveness, readiness, startup)
- `ROLLING_UPDATE_MAX_PERCENT` (opcional): `maxSurge`/`maxUnavailable` de la estrategia RollingUpdate. Default: `"25%"`

#### Para CronJobs
- `CRONJOB_SCHEDULE`: Expresion cron
- `SUSPEND_CRONJOB`: Suspender o no

### Flujo de Datos ConfigMap/Secret

1. Si existe `configuraciones.properties` → Se crea ConfigMap
2. Si existe `secrets.properties` → Se crea Secret
3. Variables `HAS_CONFIGMAP` y `HAS_SECRET` se establecen
4. En `kustomizePatchingUnified()` o `kustomizePatchingCronJob()`:
   - Si las variables son "true", se montan automaticamente como `envFrom`

### External Secrets

Requiere:
1. External Secrets Operator instalado en el cluster
2. ServiceAccount con IRSA configurado
3. Rol IAM con permisos para Secrets Manager
4. Secretos existentes en AWS Secrets Manager

### Healthchecks de Ingress

Para Ingress tipo "group":
- `healthcheck-timeout` se calcula automaticamente como `LIVENESS_PERIOD_SEC - 1`
- Esto asegura que el timeout sea menor que el intervalo

### Validaciones

- `kustomizePatchingCronJob()` valida la expresion cron usando `validateFunctions.validateCronSchedule()`
- `nullOrEmpty()` valida variables requeridas antes de generar recursos

---

## Dependencias

- **Kustomize**: Para construccion de manifiestos
- **kubectl**: Para generacion dry-run de ConfigMaps y Secrets
- **dos2unix**: Para normalizar archivos de configuracion
- **validateFunctions**: Biblioteca para validaciones (expresiones cron, etc.)
- **AWS CLI** (indirecto): Para External Secrets con AWS Secrets Manager

---

## Troubleshooting

### Error: "La variable 'X' es nula o vacia"

**Causa**: Variable de entorno requerida no esta definida

**Solucion**: Definir la variable en el bloque `environment` del pipeline

### ConfigMap o Secret no se monta automaticamente

**Causa**: Archivos `configuraciones.properties` o `secrets.properties` no existen cuando se ejecuta la funcion

**Solucion**: Crear los archivos antes de llamar a `kustomizeProcess()`

### Ingress no se crea

**Causa**: `INGRESS_TYPE` y `ROUTE_PATH` deben estar ambos definidos

**Solucion**: Asegurarse de que ambas variables esten configuradas

### CronJob tiene formato incorrecto

**Causa**: Expresion cron invalida en `CRONJOB_SCHEDULE`

**Solucion**: Usar formato valido (ej: "0 2 * * *") - La validacion lanzara error especifico

**Tags:** `#kubernetes`, `#kustomize`, `#manifests`, `#deployment`, `#cronjob`, `#ingress`, `#hpa`, `#configmap`, `#secrets`, `#aws`, `#eks`, `#jenkins`, `#pipeline`