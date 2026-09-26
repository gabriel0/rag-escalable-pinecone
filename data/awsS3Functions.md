# Funcion para gestion de objetos en buckets S3
- Copia
- Elimina
- Lista
- Sincroniza

## Uso de endpoints (manual o automatico)

Esta libreria usa `vars/awsEndpointUtils.groovy` para resolver endpoints e inyectar `--endpoint-url` en comandos `aws s3` y `aws s3api`.

- Opcion 1 (manual): definir `AWS_BUCKET_ENDPOINT` (o `AWS_S3_ENDPOINT` para compatibilidad legacy).
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true`, que detecta `com.amazonaws.<region>.s3` y completa `AWS_BUCKET_ENDPOINT`.
- Para S3 Interface VPC endpoint con DNS wildcard (`*.vpce-...`), `awsEndpointUtils.groovy` transforma el DNS a un host valido para AWS CLI.
- Si no hay variable ni descubrimiento, se usa el endpoint publico de S3.

Prioridad de resolucion en `buildEndpointArg`:

  1. Parametro `endpoint` de la funcion (si se envia).
  2. `AWS_S3_VPCE_DNS_SUFFIX` + nombre de bucket del metodo.
  3. `AWS_BUCKET_ENDPOINT`.
  4. `AWS_S3_ENDPOINT`.

Ejemplos:

```groovy
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: override manual
// env.AWS_BUCKET_ENDPOINT = "https://mi-endpoint-fijo.s3.us-east-1.amazonaws.com"
```

## Requisitos
**Metodos principales:**
- N/A

**Metodos secundarios:**
- copyToBucket: Copia un archivo/directorio desde/hacia un directorio/bucket s3.
- listFiles: Lista el contenido de un bucket, util a la hora de depurar/probar.
- fileExists: Valida si existe un archivo/directorio en un bucket, util a la hora de hacer comprobaciones.
- sync: Realiza un sync de directorio/bucket desde/hacia directorio/bucket, con multiples opciones de borrado y/o exclusion.
- deleteFromBucket: Elimina archivos/directorios de un bucket s3.

## Parametros
- Estan documentados en la libreria

## Usos

- copyToBucket:

```javascript
    stage('TrivyReport -- Upload S3') {
        steps {
            script {
                try {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-s3-credentials', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        dir("application"){
                            trivyFunctions.trivyJsonToCsv(env.SERVICE_NAME, env.BUILD_NUMBER, env.ENVIRONMENT, "reportetrivy.json", "reportetrivy.csv")
                            awsS3Functions.copyToBucket("demo-devsecops-bucket", "trivy_${SERVICE_NAME}_${ENVIRONMENT}_report.csv")
                        }
                    }
                } catch (Exception e) {
                    env.MENSAJE = env.MENSAJE ? "Pipeline: Problemas Trivy / Subida S3 ${env.MENSAJE}" : "Pipeline: Problemas Trivy / Subida S3"
                    println "${env.MENSAJE}\n Detalles:\n${e.message}"
                }
            }
        }
    }
```

- sync:

```javascript
    stage('sync S3') {
        steps {
            script {
                try {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-s3-credentials', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        awsS3Functions.sync("application","demo-devsecops-bucket","application",true,["*.tmp"])
                    }
                } catch (Exception e) {
                    env.MENSAJE = env.MENSAJE ? "Pipeline: Problemas sync S3 ${env.MENSAJE}" : "Pipeline: Problemas sync S3"
                    println "${env.MENSAJE}\n Detalles:\n${e.message}"
                }
            }
        }
    }
```
**Tags:** `#aws`, `#aws-s3`