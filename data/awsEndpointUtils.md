# Utilidades de endpoints AWS

Esta libreria centraliza la resolucion e inyeccion de `--endpoint-url` para comandos AWS CLI usados por las demas librerias.

## Variables soportadas

| Variable de entorno    | Servicio                |
|------------------------|-------------------------|
| `AWS_ECR_ENDPOINT`     | ECR (Elastic Container Registry) |
| `AWS_SM_ENDPOINT`      | Secrets Manager         |
| `AWS_BUCKET_ENDPOINT`  | S3 / Buckets            |
| `AWS_ECS_ENDPOINT`     | ECS (Elastic Container Service) |
| `AWS_EKS_ENDPOINT`     | EKS (Elastic Kubernetes Service) |
| `AWS_LOGS_ENDPOINT`    | CloudWatch Logs         |
| `AWS_LAMBDA_ENDPOINT`  | Lambda                  |
| `AWS_DYNAMODB_ENDPOINT`| DynamoDB                |

## Mapeo servicio -> variable

- `ecr` -> `AWS_ECR_ENDPOINT`
- `secretsmanager`, `secretm`, `sm` -> `AWS_SM_ENDPOINT`
- `bucket`, `s3`, `s3api` -> `AWS_BUCKET_ENDPOINT`
- `ecs` -> `AWS_ECS_ENDPOINT`
- `eks` -> `AWS_EKS_ENDPOINT`
- `logs` -> `AWS_LOGS_ENDPOINT`
- `lambda` -> `AWS_LAMBDA_ENDPOINT`
- `dynamodb` -> `AWS_DYNAMODB_ENDPOINT`

## Funciones

- `endpointEnvVarName(service)`: devuelve el nombre de variable de entorno correspondiente al servicio.
- `endpointArg(service)`: devuelve `--endpoint-url <valor>` o cadena vacia si no aplica.
- `appendEndpointToCommand(command, service)`: agrega endpoint a un comando `aws <service>` si no tiene uno definido.
- `applyAwsEndpoints(command)`: aplica endpoints a todos los servicios soportados dentro del comando.
- `discoverAwsEndpoints(...)`: consulta VPC endpoints disponibles en la cuenta/region y setea automaticamente las variables de entorno correspondientes.

## Comportamiento general

- Si la variable de endpoint existe y no es nula/vacia, se usa endpoint custom (VPC o personalizado).
- Si no existe, el CLI usa los endpoints publicos de AWS.
- Si el comando ya incluye `--endpoint-url`, no se sobrescribe.

## Comportamiento especifico para S3 (Interface VPC Endpoint)

Los VPC Interface Endpoints de S3 entregan entradas DNS con wildcard (`*.vpce-xxx.s3.region.vpce.amazonaws.com`). El CLI de AWS no acepta URLs con `*`, por lo que `discoverAwsEndpoints` transforma esa entrada reemplazando `*.` por `bucket.`, resultando en:

```
https://bucket.vpce-xxx.s3.us-east-1.vpce.amazonaws.com
```

Esta URL se asigna a `AWS_BUCKET_ENDPOINT`. Al ejecutar un comando como `aws s3api head-bucket --bucket mi-bucket`, el CLI resuelve el hostname como `mi-bucket.bucket.vpce-xxx.s3.us-east-1.vpce.amazonaws.com`, que coincide con el wildcard `*.bucket.vpce-xxx...` del certificado SSL del endpoint.

## Descubrimiento automatico

```groovy
awsEndpointUtils.discoverAwsEndpoints(
    vpcId  : env.VPC_ID,    // opcional, best-effort por region si no se indica
    region : env.AWS_REGION,
    overwrite: false        // no sobreescribe variables ya definidas
)
```

Servicios descubiertos automaticamente:
- `com.amazonaws.<region>.ecr.api` -> `AWS_ECR_ENDPOINT`
- `com.amazonaws.<region>.secretsmanager` -> `AWS_SM_ENDPOINT`
- `com.amazonaws.<region>.s3` -> `AWS_BUCKET_ENDPOINT`
- `com.amazonaws.<region>.ecs` -> `AWS_ECS_ENDPOINT`
- `com.amazonaws.<region>.eks` -> `AWS_EKS_ENDPOINT`
- `com.amazonaws.<region>.logs` -> `AWS_LOGS_ENDPOINT`
- `com.amazonaws.<region>.lambda` -> `AWS_LAMBDA_ENDPOINT`
- `com.amazonaws.<region>.dynamodb` -> `AWS_DYNAMODB_ENDPOINT`

## Ejemplo rapido

```groovy
def cmd = "timeout 60 aws ecr describe-repositories --output json"
def cmdFinal = awsEndpointUtils.applyAwsEndpoints(cmd)
sh(script: cmdFinal, returnStdout: true)
```

## Librerias que usan esta utilidad

`awsEcrFunctions`, `awsEcsFunctions`, `awsLogsFunctions`, `awsS3Functions`, `awsSecretManager`, `awsLambdaFunctions`, `dynamoDbFunctions`, `k8sFunctions` y flujos que invocan `validateFunctions`.
