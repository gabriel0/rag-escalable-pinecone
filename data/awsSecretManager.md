# Funciones de AWS Secrets Manager

Esta libreria proporciona funciones para interactuar con AWS Secrets Manager, facilitando la obtencion y gestion de secretos directamente desde los pipelines de Jenkins.

## Uso de endpoints (manual o automatico)

Esta libreria se integra con `vars/awsEndpointUtils.groovy` para resolver e inyectar `--endpoint-url` en comandos `aws secretsmanager`.

- Variable soportada: `AWS_SM_ENDPOINT`.
- Opcion 1 (manual): definir `AWS_SM_ENDPOINT` en el pipeline.
- Opcion 2 (automatica): ejecutar `awsEndpointUtils.discoverAwsEndpoints(...)` con `AWS_DISCOVER_ENDPOINTS=true` para detectar `com.amazonaws.<region>.secretsmanager`.
- Si `AWS_SM_ENDPOINT` existe y no es nula/vacia, se agrega `--endpoint-url <valor>`.
- Si no existe, se usa endpoint publico AWS.

Ejemplo:

```groovy
env.AWS_DISCOVER_ENDPOINTS = "true"
awsEndpointUtils.discoverAwsEndpoints(region: env.AWS_REGION)

// Opcional: override manual
// env.AWS_SM_ENDPOINT = "https://vpce-xxxx.secretsmanager.us-east-1.vpce.amazonaws.com"
```

## `mapSecretEnvFile`

Obtiene un secreto de AWS Secrets Manager y crea un archivo `.env` local a partir de su contenido. El secreto en AWS debe ser de tipo "Otro tipo de secreto" y su valor debe ser un JSON de clave-valor.

### Parametros

- `config` (Map): Un mapa de configuracion que debe contener la siguiente clave:
  - `secretArn` (String, **Obligatorio**): El ARN completo del secreto en AWS Secrets Manager que se desea obtener.

### Requisitos Previos

1.  **AWS CLI:** El agente de Jenkins donde se ejecute el pipeline debe tener la AWS CLI instalada y configurada.
2.  **Credenciales de AWS:** El pipeline debe tener acceso a credenciales de AWS con el permiso `secretsmanager:GetSecretValue` para el ARN del secreto especificado. Esto se logra tipicamente con el bloque `withCredentials`.
3.  **Formato del Secreto:** El secreto en AWS Secrets Manager debe ser de tipo **"Otro tipo de secreto"** y su contenido debe ser un JSON valido con una estructura de clave-valor.

    **Ejemplo de valor del secreto en AWS:**
    ```json
    {
      "DB_USER": "admin_user",
      "DB_PASSWORD": "a_very_secure_password_123!",
      "API_KEY": "abcdef123456"
    }
    ```

### Salida

- Crea un archivo llamado `.env` en el directorio de trabajo actual del pipeline.
- El archivo `.env` contendra las claves y valores del JSON del secreto, una por linea.
- Los permisos del archivo `.env` se establecen en `600` (lectura y escritura solo para el propietario).

**Ejemplo del archivo `.env` generado:**
```
DB_USER=admin_user
DB_PASSWORD=a_very_secure_password_123!
API_KEY=abcdef123456
```

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Obtener Secretos') {
    steps {
        script {
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'ID_CREDENCIALES_AWS', accessKeyVariable: 'AWS_ACCESS_KEY_ID', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']]) {
                awsSecretManager.mapSecretEnvFile([
                    secretArn: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:mi-app/mi-secreto-XXXXXX'
                ])
            }
        }
    }
}
```