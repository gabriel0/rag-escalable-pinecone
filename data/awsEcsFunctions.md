# Funcion para gestion de ECS
- Creacion
- Eliminacion

## Uso de endpoints (manual o automatico)

Esta libreria usa `vars/awsEndpointUtils.groovy` para resolver endpoints e inyectar `--endpoint-url` en comandos AWS CLI.

- Variables soportadas:
  - `AWS_ECS_ENDPOINT` para comandos `aws ecs`
  - `AWS_LOGS_ENDPOINT` para comandos `aws logs` usados por la libreria
  - `AWS_EKS_ENDPOINT` para `aws eks update-kubeconfig` (cuando aplica)
- Opcion 1 (manual): definir una o varias variables `AWS_*_ENDPOINT` en el pipeline.
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true` para autodescubrir los endpoints de la region.
- Si una variable existe y no es nula/vacia, se agrega `--endpoint-url <valor>`.
- Si no existe, se mantiene el comportamiento default contra endpoints publicos AWS.

Ejemplo:

```groovy
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: overrides manuales puntuales
// env.AWS_ECS_ENDPOINT = "https://vpce-xxxx.ecs.us-east-1.vpce.amazonaws.com"
// env.AWS_LOGS_ENDPOINT = "https://vpce-xxxx.logs.us-east-1.vpce.amazonaws.com"
// env.AWS_EKS_ENDPOINT = "https://vpce-xxxx.eks.us-east-1.vpce.amazonaws.com"
```

## Requisitos
**Metodos principales:**
- call
    * Metodo principal, que orquesta las funciones para crear/actualizar una task definition e implementarla en un cluster de ECS

**Metodos secundarios:**
- createTaskDefinitionFile
    * Funcion secundaria que crea un task definition, en caso que existieran archivos de configuraciones y/o secretos los mismos son utilizados como entrada de datos para configurar las variables de entorno pertinentes.
- checkServiceExists:
    * Funcion secundaria que valida la existencia de un service, este funcion es util para determinar en base a su respuesta si debemos actualizar o cerar un service.
- validateTaskDeployment:
    * Funcion que orquesta varias funciones secundarias, para determinar el estado del despliegue del task/service.
- registerTaskDefinition:
    * Registra una nueva task definition, utilizando el archivo json creado por la funcion "createTaskDefinitionFile", devuelve el arn de la task definition para ser utilizada en la validacion del despliegue para determinar si se implemento correctamente o no.
- deleteService
- waitForServiceDeletion
- updateService:
    * Si el servicio ya existe, se actualiza el task definition actual mediante esta funcion.
- createService
    * Si el servicio no existe, se crea el task definition mediante esta funcion.
- getDeploymentStatus:
    * Esta funcion obtiene el estado del deployment de un task, es utilizada por validateTaskDeployment para realizar un loop ciclico esperando que el despliegue finalice (bien o mal).
- checkTasksRunning
- getTaskLogs
- getDeploymentLogs:
    * Esta funcion obtiene el estado del deployment de un task, es utilizada por validateTaskDeployment para obtener los logs del despliegue si el mismo falla.


# Gestion Automatica de Target Groups y Listener Rules en ECS

## Descripcion

Esta mejora permite que el pipeline de ECS cree automaticamente Target Groups y reglas de Listener en el ALB cuando `TARGET_GROUP_ARN` no esta definido. Esto proporciona mayor autonomia al pipeline para dar de alta nuevos servicios con URLs automaticamente gestionadas.

## Flujo de Trabajo

### Escenario 1: Target Group Pre-existente (Comportamiento Actual)
```
┌──────────────────────┐
│  TARGET_GROUP_ARN    │
│  esta definido       │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│  Crear/Actualizar    │
│  Servicio ECS        │
│  con TG existente    │
└──────────────────────┘
```

### Escenario 2: Target Group Automatico (Nueva Funcionalidad)
```
┌──────────────────────┐
│  TARGET_GROUP_ARN    │
│  NO esta definido    │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│  Crear Target Group  │
│  automaticamente     │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│  ¿LISTENER_ARN       │
│  esta definido?      │
└────┬─────────────┬───┘
     │ Si          │ No
     v             v
┌──────────┐  ┌────────────────┐
│ Crear    │  │ Advertencia:   │
│ Listener │  │ No se crea     │
│ Rule     │  │ regla de ALB   │
└────┬─────┘  └────────────────┘
     │
     v
┌──────────────────────┐
│  Crear/Actualizar    │
│  Servicio ECS        │
│  con TG creado       │
└──────────────────────┘
```

## Variables de Entorno

### Variables Requeridas (existentes)
Estas variables ya son requeridas en el pipeline actual:

- `SERVICE_NAME`: Nombre del servicio
- `CLUSTER_NAME`: Nombre del cluster ECS
- `CONTAINER_PORT`: Puerto del contenedor
- `VPC_SUBNETS`: Subnets de la VPC
- `SECURITY_GROUPS`: Security groups del servicio
- `SERVICE_REPLICAS`: Numero de replicas
- `MIN_HEALTH_PERCENT`: Porcentaje minimo de salud
- `MAX_HEALTH_PERCENT`: Porcentaje maximo de salud

### Nuevas Variables Requeridas para Auto-Gestion

#### VPC_ID (OBLIGATORIO para auto-gestion)
ID de la VPC donde se creara el Target Group.

```bash
VPC_ID=vpc-0abcd1234efgh5678
```

#### LISTENER_ARN (OPCIONAL pero recomendado)
ARN del Listener del ALB donde se crearan las reglas de routing. Si no se define, el Target Group se crea pero no se configura el routing automaticamente.

```bash
LISTENER_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2
```

### Variables de Routing (al menos una requerida si LISTENER_ARN esta definido)

#### SERVICE_PATH
Path pattern para routing basado en URL path. Soporta wildcards.

```bash
# Ejemplos:
SERVICE_PATH=/api/*
SERVICE_PATH=/grafana/*
SERVICE_PATH=/metrics/*
```

#### SERVICE_HOST
Host header para routing basado en dominio.

```bash
# Ejemplos:
SERVICE_HOST=api.example.com
SERVICE_HOST=grafana.mycompany.com
SERVICE_HOST=*.api.example.com
```

**Nota**: Puedes definir ambas variables para crear una regla con multiples condiciones (path Y host).

### Variables Opcionales de Configuracion

#### LISTENER_RULE_PRIORITY
Prioridad de la regla en el Listener. Si no se define, se calcula automaticamente (siguiente numero disponible).

```bash
LISTENER_RULE_PRIORITY=50
```

#### Health Check del Target Group

Estas variables ya existen en el pipeline pero ahora se usan tambien para configurar el Target Group:

```bash
HEALTH_CHECK_PATH=/health                    # Default: /
HEALTH_CHECK_INTERVAL=30                     # Default: 30 segundos
HEALTH_CHECK_TIMEOUT=15                      # Default: 15 segundos
HEALTH_CHECK_HEALTHY_THRESHOLD=2             # Default: 2
HEALTH_CHECK_UNHEALTHY_THRESHOLD=3           # Default: 3
```

## Ejemplos de Configuracion

### Ejemplo 1: Servicio con Target Group Pre-existente (Sin cambios)

**Archivo**: `configs/demo/test/demo-grafana/services.env`

```bash
CLUSTER_NAME=demo-ecs-grafana
TARGET_GROUP_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/demo-target-group/abc123
CONTAINER_PORT=3000
LOG_GROUP_NAME=/aws/ecs/demo-ecs-grafana
TASK_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-grafana
EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-grafana
HEALTH_CHECK_PATH=/api/health
```

**Comportamiento**: El pipeline usa el Target Group existente, igual que antes.

---

### Ejemplo 2: Nuevo Servicio con Auto-Gestion Completa

**Archivo**: `configs/demo/test/demo-newservice/services.env`

```bash
CLUSTER_NAME=demo-ecs-cluster
# TARGET_GROUP_ARN no definido - se creara automaticamente
CONTAINER_PORT=8080
LOG_GROUP_NAME=/aws/ecs/demo-ecs-newservice
TASK_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-app
EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-app
HEALTH_CHECK_PATH=/health

# Nuevas variables para auto-gestion
LISTENER_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2
SERVICE_PATH=/api/newservice/*
```

**Archivo**: `configs/demo/test/environment.env`

```bash
VPC_SUBNETS=subnet-0123456789abcdef0,subnet-0fedcba9876543210
SECURITY_GROUPS=sg-0123456789abcdef0
VPC_ID=vpc-0abcd1234efgh5678  # Nueva variable requerida
# ... resto de variables
```

**Comportamiento**:
1. Se crea un Target Group llamado `demo-newservice-tg`
2. Se crea una regla de Listener con path pattern `/api/newservice/*`
3. Se crea el servicio ECS apuntando al nuevo Target Group
4. El servicio queda accesible en `http://alb-dns/api/newservice/`

---

### Ejemplo 3: Servicio con Routing por Host Header

**Archivo**: `configs/demo/prod/demo-api/services.env`

```bash
CLUSTER_NAME=demo-ecs-cluster-prod
# TARGET_GROUP_ARN no definido
CONTAINER_PORT=3000
LOG_GROUP_NAME=/aws/ecs/demo-ecs-api
TASK_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-api
EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-api
HEALTH_CHECK_PATH=/api/health

# Routing por host
LISTENER_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/prod-alb/...
SERVICE_HOST=api.mycompany.com
```

**Comportamiento**:
1. Se crea un Target Group
2. Se crea una regla de Listener con host header `api.mycompany.com`
3. El servicio queda accesible en `http://api.mycompany.com`

---

### Ejemplo 4: Servicio con Path Y Host (Regla Combinada)

```bash
# En services.env
LISTENER_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/...
SERVICE_PATH=/metrics/*
SERVICE_HOST=monitoring.mycompany.com
```

**Comportamiento**:
- Se crea una regla que requiere AMBAS condiciones
- Solo el trafico a `http://monitoring.mycompany.com/metrics/*` llegara al servicio

---

### Ejemplo 5: Solo Target Group sin Listener (Casos especiales)

```bash
# En environment.env
VPC_ID=vpc-0abcd1234efgh5678

# En services.env - NO definir LISTENER_ARN
CLUSTER_NAME=demo-ecs-cluster
CONTAINER_PORT=8080
# ... resto de configuracion sin LISTENER_ARN, SERVICE_PATH, ni SERVICE_HOST
```

**Comportamiento**:
1. Se crea un Target Group
2. Se muestra una advertencia indicando que no se creara regla de Listener
3. El Target Group puede ser configurado manualmente despues o usado para otros propositos

## Nombres Generados Automaticamente

### Target Group
- **Formato**: `{SERVICE_NAME}-tg`
- **Limite**: Maximo 32 caracteres (AWS limitation)
- **Ejemplo**: `demo-grafana-tg`

Si el nombre excede 32 caracteres, se trunca automaticamente.

### Tags Aplicados Automaticamente

**Target Group**:
```
Name: {SERVICE_NAME}-tg
Service: {SERVICE_NAME}
ManagedBy: Jenkins
Environment: {ENVIRONMENT}
```

**Listener Rule**:
```
Name: {SERVICE_NAME}-rule
Service: {SERVICE_NAME}
ManagedBy: Jenkins
Environment: {ENVIRONMENT}
```

## Casos de Uso

### 1. Migracion Gradual
Manten servicios existentes con `TARGET_GROUP_ARN` definido mientras creas nuevos servicios con auto-gestion.

### 2. Entornos de Desarrollo
En entornos de test/dev, puedes crear y destruir servicios rapidamente sin necesidad de configurar infraestructura de ALB manualmente.

### 3. Microservicios Dinamicos
Facilita la creacion de multiples microservicios con sus propios endpoints en el mismo ALB.

### 4. Self-Service para Equipos
Los equipos pueden desplegar nuevos servicios definiendo solo las variables de routing, sin depender del equipo de infraestructura.

## Validaciones y Manejo de Errores

### Target Group
- ✅ Si el Target Group ya existe con el mismo nombre, se reutiliza (idempotente)
- ✅ Valida que `VPC_ID` este definido
- ❌ Si falla la creacion del TG, el pipeline se detiene con error

### Listener Rule
- ✅ Si ya existe una regla apuntando al mismo TG, se reutiliza (idempotente)
- ✅ Calcula automaticamente la siguiente prioridad disponible
- ⚠️ Si falla la creacion de la regla, muestra advertencia pero continua (el servicio se crea, pero puede no recibir trafico del ALB)

## Retrocompatibilidad

**100% Compatible**: El pipeline sigue funcionando exactamente igual para servicios que tienen `TARGET_GROUP_ARN` definido. No hay cambios breaking.

## Logs y Debugging

El pipeline imprime informacion detallada:

```
[Informacion] TARGET_GROUP_ARN no definido. Creando Target Group automaticamente...
[Informacion] Creando Target Group para demo-newservice
[OK] Target Group creado exitosamente: arn:aws:elasticloadbalancing:...
[Informacion] Tags agregados al Target Group
[Informacion] Creando regla de Listener para demo-newservice
[Informacion] Condicion de path agregada: /api/newservice/*
[Informacion] Prioridad calculada automaticamente: 5
[OK] Regla de Listener creada exitosamente: arn:aws:elasticloadbalancing:...
[Informacion] Prioridad: 5
[Informacion] Path pattern: /api/newservice/*
```

## Recreacion de Servicios Existentes

Si tienes un servicio **ya existente** y quieres migrar a la gestion automatica de Target Groups, o necesitas cambiar el Target Group asociado a un servicio, necesitas recrearlo. La funcion `recreateService()` facilita este proceso.

### Escenario 3: Recreacion de Servicio Existente
```
┌──────────────────────┐
│  Servicio existe     │
│  en ECS              │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│  ¿FORCE_RECREATE     │
│  = true?             │
└────┬─────────────┬───┘
     │ Si          │ No
     v             v
┌──────────┐  ┌────────────────┐
│ Eliminar │  │ Update normal  │
│ servicio │  │ (sin cambiar   │
└────┬─────┘  │  Target Group) │
     │        └────────────────┘
     v
┌──────────────────────┐
│  Esperar eliminacion │
└──────────┬───────────┘
           │
           v
┌──────────────────────┐
│  Crear servicio      │
│  (con nueva logica   │
│  de auto-gestion)    │
└──────────────────────┘
```

### Opcion 1: Usar la variable `FORCE_RECREATE` (Recomendado)

Agrega esta variable a tu configuracion para forzar la recreacion del servicio:

**Archivo**: `configs/demo/test/demo-grafana/services.env`

```bash
CLUSTER_NAME=demo-ecs-grafana
#TARGET_GROUP_ARN=arn:aws:...  # Comentar el Target Group existente
FORCE_RECREATE=true             # Forzar recreacion UNA VEZ
CONTAINER_PORT=3000
LOG_GROUP_NAME=/aws/ecs/demo-ecs-grafana
TASK_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-grafana
EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/demo-role-grafana
HEALTH_CHECK_PATH=/api/health

# Nuevas variables para auto-gestion
LISTENER_ARN=arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo-alb/abc123/def456
SERVICE_PATH=/*
SERVICE_HOST=metrics.example.com
```

**Importante**:
- ⚠️ Esto causara **downtime temporal** mientras se elimina y recrea el servicio (tipicamente 1-3 minutos)
- ✅ Solo usar en entornos de test/dev o durante ventanas de mantenimiento
- ✅ **Despues de la primera ejecucion exitosa, QUITAR `FORCE_RECREATE=true`** para evitar recreaciones accidentales
- ✅ El servicio se creara con el nuevo Target Group autogestionado

**Logs esperados con `FORCE_RECREATE=true`**:
```
[Informacion] Verificando si el servicio demo-grafana debe ser recreado...
[Advertencia] El servicio demo-grafana ya existe.
[Advertencia] La recreacion eliminara el servicio existente y lo volvera a crear.
[Advertencia] Esto causara downtime temporal.
[Informacion] FORCE_RECREATE=true detectado. Procediendo con la recreacion...
Eliminando servicio demo-grafana
[informacion] El servicio demo-grafana aun esta pendiente de eliminacion. Esperando 10 segundos..
[OK] El servicio demo-grafana fue eliminado
Creando servicio demo-grafana
[Informacion] TARGET_GROUP_ARN no definido. Creando Target Group automaticamente...
[Informacion] Creando Target Group para demo-grafana
[OK] Target Group creado exitosamente: arn:aws:elasticloadbalancing:...
[Informacion] Creando regla de Listener para demo-grafana
[Informacion] Condicion de path agregada: /*
[Informacion] Condicion de host agregada: metrics.example.com
[Informacion] Prioridad calculada automaticamente: 2
[OK] Regla de Listener creada exitosamente: arn:aws:elasticloadbalancing:...
[Informacion] Servicio demo-grafana creado con exito.
```

**Logs cuando `FORCE_RECREATE` NO esta definido**:
```
[Informacion] Verificando si el servicio demo-grafana debe ser recreado...
[Advertencia] El servicio demo-grafana ya existe.
[Advertencia] La recreacion eliminara el servicio existente y lo volvera a crear.
[Advertencia] Esto causara downtime temporal.
[Informacion] Para recrear el servicio, define FORCE_RECREATE=true en tu configuracion.
[Informacion] Procediendo con update normal del servicio existente...
Actualizando servicio demo-grafana
[Informacion] Servicio demo-grafana actualizado con exito.
```

### Opcion 2: Eliminar el servicio manualmente via AWS CLI

Si prefieres tener control manual del proceso:

```bash
# 1. Eliminar el servicio
aws ecs delete-service \
  --cluster demo-ecs-grafana \
  --service demo-grafana \
  --force \
  --region us-east-1

# 2. Esperar a que se elimine completamente
aws ecs wait services-inactive \
  --cluster demo-ecs-grafana \
  --services demo-grafana \
  --region us-east-1

# 3. Ejecutar el pipeline de nuevo (creara el servicio con auto-gestion)
```

### Funcion `recreateService()` - Metodo Avanzado

La funcion `recreateService()` fue agregada para soportar el flujo de recreacion. Se invoca automaticamente desde el metodo `call()` principal.

**Comportamiento**:
1. Si el servicio **NO existe** → llama a `createService()` (con auto-gestion de TG si aplica)
2. Si el servicio **existe** y `FORCE_RECREATE=true` → llama a `deleteService()` + `createService()`
3. Si el servicio **existe** y `FORCE_RECREATE` no esta definido → llama a `updateService()` (sin cambiar TG)

**Modificacion del flujo principal** (ya aplicada en el codigo):

```groovy
// En awsEcsFunctions.groovy - Metodo call()
def call(String pathConfiguracion = ".") {
    try {
        validateFunctions.checkAwsEndpoint('ecs')
        pathSet()
        createTaskDefinitionFile("${pathConfiguracion}/configuraciones.properties","${pathConfiguracion}/secrets.properties")
        def taskDefInfo = registerTaskDefinition()

        // ANTES (comportamiento original):
        // checkServiceExists() ? updateService(taskDefInfo.taskDefinitionArn) : createService(taskDefInfo.taskDefinitionArn)

        // AHORA (con soporte para FORCE_RECREATE):
        recreateService(taskDefInfo.taskDefinitionArn)

        if (!validateTaskDeployment(taskDefInfo.taskDefinitionArn)) {
            throw new Exception("El despliegue del servicio ${env.SERVICE_NAME} fallo.")
        }
    } catch (Exception e) {
        handleError("Pipeline: Error en proceso ECS.\n Detalles: ${e.message}")
    }
}
```

### Cuando usar `FORCE_RECREATE`

✅ **Usar cuando**:
- Necesitas cambiar el Target Group de un servicio existente
- Quieres migrar de Target Group manual a auto-gestionado
- Necesitas cambiar parametros que no se pueden modificar con update (ej: tipo de Target Group)
- Estas en entorno de test/dev y quieres probar la nueva funcionalidad

❌ **NO usar cuando**:
- Solo necesitas actualizar la Task Definition (usa update normal)
- Estas en produccion sin ventana de mantenimiento (causara downtime)
- No estas seguro de los cambios (prueba primero en test)

### Checklist para Migracion de Servicio Existente

1. ✅ Verificar que `VPC_ID` este definido en `environment.env`
2. ✅ Agregar `LISTENER_ARN`, `SERVICE_PATH` y/o `SERVICE_HOST` en `services.env`
3. ✅ Comentar `TARGET_GROUP_ARN` existente en `services.env`
4. ✅ Agregar `FORCE_RECREATE=true` en `services.env`
5. ✅ Ejecutar el pipeline y verificar logs
6. ✅ Validar que el servicio se cree correctamente y reciba trafico
7. ✅ **IMPORTANTE**: Quitar `FORCE_RECREATE=true` de `services.env` despues del exito
8. ✅ Commit de los cambios de configuracion (sin `FORCE_RECREATE`)

## Permisos IAM Requeridos

Asegurate de que las credenciales de AWS (`SERVICE_CREDS`) tengan los siguientes permisos adicionales:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:CreateRule",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeListeners",
        "ecs:DeleteService"
      ],
      "Resource": "*"
    }
  ]
}
```

## Resumen de Funciones

### Funciones Principales
- **`call()`**: Metodo principal que orquesta el proceso completo de ECS
- **`recreateService()`**: Nueva funcion que decide si crear, actualizar o recrear un servicio basado en `FORCE_RECREATE`

### Funciones de Gestion de Servicios
- **`createService()`**: Crea un nuevo servicio ECS (con auto-gestion de TG si aplica)
- **`updateService()`**: Actualiza un servicio existente (solo Task Definition)
- **`deleteService()`**: Elimina un servicio ECS
- **`waitForServiceDeletion()`**: Espera hasta que el servicio se elimine completamente
- **`checkServiceExists()`**: Verifica si un servicio existe

### Funciones de Auto-Gestion (Nuevas)
- **`createTargetGroup()`**: Crea automaticamente un Target Group para el servicio
- **`createListenerRule()`**: Crea automaticamente una regla de Listener en el ALB

### Funciones de Task Definition
- **`createTaskDefinitionFile()`**: Genera el archivo JSON de Task Definition
- **`registerTaskDefinition()`**: Registra la Task Definition en AWS

### Funciones de Validacion y Logs
- **`validateTaskDeployment()`**: Valida que el despliegue se complete exitosamente
- **`getDeploymentStatus()`**: Obtiene el estado del despliegue
- **`getDeploymentLogs()`**: Obtiene logs en caso de fallo
- **`checkTasksRunning()`**: Verifica si las tareas estan corriendo
- **`getTaskLogs()`**: Obtiene logs de las tareas

**Tags:** `#aws`, `#aws-ecs`, `#alb`, `#target-groups`, `#automation`