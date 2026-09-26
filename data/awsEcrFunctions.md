# Funcion para gestion de ECR
- Creacion
- Eliminacion
- Configuracion de ciclo de vida

## Uso de endpoints (manual o automatico)

Esta libreria se integra con `vars/awsEndpointUtils.groovy` para resolver e inyectar `--endpoint-url` en comandos `aws ecr`.

- Variable de endpoint manual: `AWS_ECR_ENDPOINT`.
- Opcion 1 (manual): definir `AWS_ECR_ENDPOINT` en el pipeline.
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true` para autodescubrir endpoints privados y poblar las variables `AWS_*_ENDPOINT`.
- Si `AWS_ECR_ENDPOINT` existe y no es nula/vacia, se agrega `--endpoint-url <valor>` y se usa endpoint privado/custom.
- Si no existe, se mantiene el endpoint publico de AWS (comportamiento por defecto).

Ejemplo:

```groovy
// Descubrimiento automatico (recomendado cuando hay VPC endpoints)
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: override manual explicito
// env.AWS_ECR_ENDPOINT = "https://vpce-xxxx.ecr.us-east-1.vpce.amazonaws.com"
```

## Requisitos
**Metodos principales:**

- mainEcr: Es el metodo principal el cual orquesta la funcionalidad completa de gestion de ECR, si se la invoca desde el pipeline realizara los siguientes pasos:

    * Verifica si existe la registry, en caso que negativo la crea.
    * Al crearla, es creada con encripcion KMS, si se le pasa como parametro el KMS KEY-ID, caso contrario se crea sin encripcion.
    * Valida que tenga la politica de retencion (lifecycle policy), caso negativo la aplica. Si tiene un lifecyclepolicy distinta a la definida en la libreria la actualiza sino la pasa por alto.

- onlyPutLifecyclePolicy: Este metodo orquesta la configuracion de una politica de retencion, utilizando los metodos secundarios (repositoryExists, isLifecyclePolicyEqual, normalizeLifecyclePolicy, )

- createWithKms: Crea el ECR encriptado con KMS, tanto la registry como el kms-key-id deben ser enviados como parametro.

- listRepositories: Lista los repositorios, todos, de la cuenta de servicio que se este usando para el login.

**Metodos secundarios:**

- delete: Elimina el ECR que se le envie como parametro.

- repositoryExists: Valida si el repositorio existe. Esta funcion es util a la hora de crear y/o borrar un repositorio validando su existencia antes de realizar operaciones.

- createEcrLifecyclePolicy: Crea un lifecyclepolicy.

- isLifecyclePolicyEqual: Valida si la registry ya tiene una politica aplicada.

- addLifecyclePolicy: Agrega la politica creada con "createEcrLifecyclePolicy".

- normalizeLifecyclePolicy: Se utiliza para eliminar la metadata al obtener el detalle de la politica, esto es util para validar si la politica actual es la misma que la politica a aplicar, ya que la metadata es dinamica y genera un falso positivo al realizar el control.

- countEncryptionTypes: Realiza un recuento de las registries y su tipo de encripcion.

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
                                    //Armar el nombre del repositorio mediante el uso de variables
                                    def REPOSITORY_NAME="${ECR_REPOSITORY}/${IMAGE_NAME}"
                                    awsEcrFunctions.mainEcr(REPOSITORY_NAME, env.KMS_KEYID_ARN)
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
**Tags:** `#aws`, `#aws-ecr`