# Funcion para gestion de cloudwatch logs insight
- Creacion de log query insights
- Eliminacion de log query insights

## Uso de endpoints (manual o automatico)

Esta libreria usa `vars/awsEndpointUtils.groovy` para resolver endpoints e inyectar `--endpoint-url` cuando ejecuta AWS CLI.

- Variables soportadas:
  - `AWS_LOGS_ENDPOINT` para comandos `aws logs`
  - `AWS_EKS_ENDPOINT` para comandos `aws eks` usados para inferencia de cluster
- Opcion 1 (manual): definir variables `AWS_*_ENDPOINT` en el pipeline.
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true` para detectar endpoints privados por region.
- Si la variable existe y no es nula/vacia, se agrega `--endpoint-url <valor>`.
- Si no existe, se usa endpoint publico AWS.

Ejemplo:

```groovy
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: overrides manuales puntuales
// env.AWS_LOGS_ENDPOINT = "https://vpce-xxxx.logs.us-east-1.vpce.amazonaws.com"
// env.AWS_EKS_ENDPOINT = "https://vpce-xxxx.eks.us-east-1.vpce.amazonaws.com"
```

## Requisitos
**Metodos principales:**

- manageLogQuery: Es el metodo principal el cual orquesta la funcionalidad completa de gestion de CloudWatch Logs Insights.

    * Verifica si ya existe el log query insight
    * Crea el log query insight si no existe

**Metodos secundarios:**

- executeCommand: Este metodo ejecuta comandos de AWS, con el control de error pertinente y sus retries.

- getLogQueriesDefinitions: Este metodo obtiene las definiciones de log queries.

- createLogQuery: Este metodo crea un log query, obteniendo una serie de parametros necesarios para la creacion del log query (Nombre de la consulta, Nombre del grupo de logs, Definicion de la consulta).

- assembleK8sPredefinedQuery: Este metodo construye una consulta predefinida para Kubernetes.

- inferLogGroupName: Este metodo intenta inferir el nombre del grupo de logs, basado en el nombre del cluster de EKS.

- deleteLogQuery: Este metodo elimina un log query.

- getLogQueryIdFromName: Este metodo obtiene el id de un log query a partir de su nombre. Este metodo es utilizado por deleteLogQuery para determinar si existe lo que va a querer eliminar y evitar un error.

- queryNameAlreadyExist: Este metodo es utilizado para controlar si el log query insight ya existe. Este metodo es utilizado por manageLogQuery para validar si la query no existe antes d eintentar crearla.

## Parametros


## Usos
Llamada a la
```javascript
        stage('Validaciones Cloud -- ECR & CW Logs Insights') {
            steps {
                script {
                    docker.image("${DOCKER_PIPELINE_RUN}/${DOCKER_PIPELINE_IMAGE}").inside(" --entrypoint=''  ") {
                        def urls = [
                            "https://api.ecr.${AWS_REGION}.amazonaws.com",
                            "https://logs.${AWS_REGION}.amazonaws.com",
                            "https://${PRINCIPAL_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com",
                            "https://logs.${AWS_REGION}.api.aws"
                        ]
                        validateFunctions.validarStatusUrls(urls)
                            try {
                                withCredentials([[
                                    $class: 'AmazonWebServicesCredentialsBinding', credentialsId: env.SERVICE_CREDS, accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                                ]]) {
                                    awsLogsFunctions.manageLogQuery(env.SERVICE_NAME, env.NAMESPACE)
                                }
                            } catch (e) {
                                env.MENSAJE = "Pipeline: Problemas creacion ecr / logs insight query cloudwatch"
                                println MENSAJE
                                error("${e.message}")
                            }
                    }
                }
            }
        }
```

**Tags:** `#aws`, `#aws-logs`, `#aws-queryinsights`