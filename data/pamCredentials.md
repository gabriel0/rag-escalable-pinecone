# Funciones de Credenciales PAM (Privileged Access Management)

Esta libreria contiene un conjunto de funciones diseñadas para interactuar con la API de BeyondTrust Privileged Access Management (PAM) y obtener credenciales de forma segura para ser utilizadas en los pipelines de Jenkins.

## Flujo de Obtencion de Credenciales

El proceso para obtener una credencial consta de los siguientes pasos, que son orquestados por la funcion principal `getPAMCredential`:

1.  **Sign-in**: Autenticacion contra la API de PAM para obtener una cookie de sesion.
2.  **Busqueda de Cuenta**: Se busca la cuenta gestionada por su nombre para obtener sus identificadores (`SystemId` y `AccountId`).
3.  **Solicitud de Acceso**: Se crea una solicitud de acceso para la cuenta, lo que genera un `RequestId`.
4.  **Obtencion de Credencial**: Se utiliza el `RequestId` para recuperar la contraseña temporal de la cuenta.

## Funciones Disponibles

### `getPAMCredential`

Funcion principal que orquesta todo el flujo para obtener una credencial de PAM. Es la funcion recomendada para usar directamente desde los pipelines.

#### Parametros

-   `params` (Map): Un mapa que contiene los siguientes parametros:
    -   `credentialID` (String, **Obligatorio**): El ID de la credencial de Jenkins (de tipo `Username/Password`) que almacena la clave de API de PAM (`Password`) y el usuario `runas` (`Username`).
    -   `pamAccountName` (String, **Obligatorio**): El nombre de la cuenta gestionada en PAM cuya credencial se desea obtener.
    -   `pamProdHostApi` (String, **Obligatorio**): La URL base de la API de PAM (ej. `https://pam.example.com/BeyondTrust/api/public/v3`).

#### Retorno

-   `String`: La credencial (contraseña) en texto plano.

#### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Ejecutar Comandos Remotos con PAM') {
    steps {
        script {
            def pamParams = [
                credentialID  : 'PAM-API-KEY-CRED',
                pamAccountName: 'usuario-svc-despliegue',
                pamProdHostApi: 'https://pam.example.com/BeyondTrust/api/public/v3'
            ]

            // Obtener la credencial
            def password = pamCredentials.getPAMCredential(pamParams)

            // Usar la credencial de forma segura
            withCredentials([string(credentialsId: 'mi-credencial-ssh-con-password', variable: 'SSH_PASSWORD', password: password)]) {
                sh 'sshpass -p $SSH_PASSWORD ssh usuario@servidor "comando"'
            }
        }
    }
}
```

---

### Funciones Auxiliares

Las siguientes funciones son utilizadas internamente por `getPAMCredential` y generalmente no necesitan ser llamadas directamente.

#### `getPAMSignIn`

Realiza el sign-in en la API de PAM para obtener una cookie de sesion.

-   **Parametros**: `credentialID`, `pamProdHostApi`.
-   **Retorno**: `String` con la cookie de sesion.
-   **Endpoint API**: `POST /Auth/SignAppin`
-   **Documentacion Oficial**: BeyondTrust - POST Auth/SignAppin

#### `getPAMManagedAccountsByAccountName`

Obtiene los detalles de una cuenta gestionada en PAM a partir de su nombre.

-   **Parametros**: `pamAccountName`, `pamCookieSession`, `pamProdHostApi`.
-   **Retorno**: `Map` con los datos de la cuenta (`systemId`, `accountId`, `systemName`, `accountName`).
-   **Endpoint API**: `GET /ManagedAccounts`
-   **Documentacion Oficial**: BeyondTrust - GET ManagedAccounts

#### `getPAMRequestByAccountID`

Solicita un ticket de acceso para una cuenta gestionada especifica.

-   **Parametros**: `pamSystemId`, `pamAccountId`, `pamCookieSession`, `pamProdHostApi`.
-   **Retorno**: `String` con el ID de la solicitud (`RequestId`).
-   **Endpoint API**: `POST /Requests`
-   **Documentacion Oficial**: BeyondTrust - POST Requests

#### `getPAMCredentialsByRequestId`

Obtiene la credencial (contraseña) asociada a una solicitud de acceso ya aprobada.

-   **Parametros**: `pamRequestId`, `pamCookieSession`, `pamProdHostApi`.
-   **Retorno**: `String` con la credencial en texto plano.
-   **Endpoint API**: `GET /Credentials/{id}`
-   **Documentacion Oficial**: BeyondTrust - GET Credentials/{id}
