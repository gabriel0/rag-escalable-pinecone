# Funciones de Fastlane para Moviles

Esta libreria contiene un conjunto de funciones diseñadas para automatizar el ciclo de vida de compilacion, firma y distribucion de aplicaciones moviles (Android e iOS) utilizando Fastlane.

## `preparo_entorno`

Prepara el entorno de compilacion para una aplicacion Android. Lee el archivo `.gradle` de la aplicacion para extraer metadatos clave y los establece como variables de entorno para ser utilizados en pasos posteriores del pipeline.

### Logica de Ejecucion

1.  Busca el archivo `.gradle` dentro del directorio `./app`.
2.  Extrae los siguientes valores utilizando `grep` y `sed`:
    - `applicationId`
    - `versionCode`
    - `versionName`
    - `sourceCompatibility` (para determinar la version de Java)
3.  Establece las siguientes variables de entorno:
    - `PACKAGE_NAME`
    - `VERSION_CODE`
    - `VERSION_NAME`
    - `COMPABILITY_JAVAVERSION`
    - `LANG_VERSION`

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Preparar Entorno') {
    steps {
        script {
            // Se asume que el codigo fuente de la app esta en ./app
            mobileFastlaneFunctions.preparo_entorno()
        }
    }
}
```

---

## `ejecucion_fastlane_signer`

Orquesta el proceso de compilacion y firma de una aplicacion Android. Esta funcion puede manejar diferentes `flavors` y tipos de `build`, y opcionalmente firmar el artefacto y subirlo a la Google Play Store.

### Parametros

- `extension` (String, **Obligatorio**): La extension del artefacto a generar. Valores validos: `apk`, `aab`.
- `buildtype` (String, **Obligatorio**): El tipo de build (ej. `Release`, `Debug`).
- `flavor` (String, **Obligatorio**): El/los `flavor(s)` a compilar, separados por espacios si son varios. La funcion iterara sobre cada uno.
- `jarsigner` (String, **Opcional**): Indica si se debe realizar una firma manual con `jarsigner`. Valores: `si`, `no`. Por defecto, Fastlane maneja la firma.
- `uploadstore` (String, **Opcional**): Indica si el artefacto (`.aab`) debe ser subido a la Google Play Store. Valores: `si`, `no`.

### Logica de Ejecucion

Para cada `flavor` proporcionado:
1.  Determina que `lane` de Fastlane ejecutar (`build_aab`, `build_sign_release`, `build_apk`, `build_apk_sign_release`) segun la `extension` y el parametro `jarsigner`.
2.  Ejecuta la `lane` correspondiente para compilar la aplicacion.
3.  Copia el artefacto generado a un directorio de artefactos (definido por `env.ARTEFACTS_DIR`).
4.  Si `uploadstore` es `si` y la extension es `aab`, sube el artefacto a la Google Play Store.
5.  Si `jarsigner` es `si`, firma la aplicacion utilizando la funcion `sign_android_app`.
6.  Limpia los archivos temporales de Fastlane.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Compilar y Firmar App') {
    steps {
        script {
            mobileFastlaneFunctions.ejecucion_fastlane_signer(
                extension: 'aab',
                buildtype: 'Release',
                flavor: 'full',
                jarsigner: 'no',
                uploadstore: 'si'
            )
        }
    }
}
```

---

## `subir_app_nexus`

Sube los artefactos de la aplicacion (`.apk`, `.aab`, `.ipa`) que se encuentren en el directorio de trabajo al repositorio de Nexus.

### Logica de Ejecucion

1.  Busca archivos con extension `.apk`, `.aab`, o `.ipa` en el workspace.
2.  Para cada archivo encontrado, determina la URL de destino en Nexus basandose en la extension.
3.  Construye la ruta de destino en Nexus usando la plataforma (`android`/`ios`), `PACKAGE_NAME`, `flavor`, `version_code` y `version_name`.
4.  Utiliza `curl` para subir el archivo al repositorio Nexus correspondiente.

### Variables de Entorno Requeridas

- `NEXUS_REPOSITORY_PROD`, `REPO_NEXUS_NAME_PROD`: Para artefactos `.aab` e `.ipa`.
- `NEXUS_REPOSITORY_TEST`, `REPO_NEXUS_NAME_NOPROD`: Para artefactos `.apk`.
- `USERNEXUS`, `PASSNEXUS`: Credenciales de Nexus.
- `PACKAGE_NAME`: Identificador del paquete de la app.

---

## `subir_app_mobsf`

Sube los artefactos (`.apk`, `.ipa`) a MobSF (Mobile Security Framework) para un analisis de seguridad.

### Logica de Ejecucion

1.  Busca archivos `.apk` o `.ipa` en el workspace.
2.  Para cada archivo, lo sube a la API de MobSF.
3.  Inicia un escaneo para el archivo subido.
4.  Espera a que el escaneo finalice, consultando el estado del reporte periodicamente.
5.  Una vez completado, descarga el reporte en formato JSON, lo procesa para generar un resumen en formato de texto y archiva ambos como artefactos del build.

### Variables de Entorno Requeridas

- `MOBSF_HOST_URL`: La URL de la instancia de MobSF.
- `MOBSF_AUTH`: El token de API para autenticarse en MobSF.

---

## `subir_app_diawi`

Sube los artefactos (`.apk`, `.ipa`) a Diawi para su distribucion y pruebas.

### Logica de Ejecucion

1.  Busca archivos `.apk` o `.ipa` en el workspace.
2.  Para cada archivo, lo sube a la API de Diawi.
3.  Espera a que el procesamiento finalice y obtiene el estado.
4.  Extrae la URL del codigo QR para la descarga.
5.  Si `ENVIAR_QR` es `si`, envia una notificacion a Google Chat con el QR.
6.  Añade la URL del QR a la variable de entorno `LISTA_QR`.

### Variables de Entorno Requeridas

- `DIAWI_TOKEN`: El token de API para Diawi.
- `ENVIAR_QR` (Opcional): Si su valor es `si`, se enviara una notificacion a Google Chat.
- `WEBHOOK_URL` (Opcional): URL del webhook de Google Chat, necesaria si `ENVIAR_QR` es `si`.

---

## `generar_keychains_temporal`

Crea y configura una keychain temporal en un agente macOS para la firma de aplicaciones iOS.

### Logica de Ejecucion

1.  Crea una nueva keychain con el nombre y contraseña especificados.
2.  La establece como la keychain por defecto.
3.  La desbloquea para que pueda ser utilizada por los procesos de firma.
4.  Añade la keychain del sistema a la lista de busqueda.

### Variables de Entorno Requeridas

- `KEYCHAIN_PASSWORD`: Contraseña para la nueva keychain.
- `KEYCHAIN_NAME`: Nombre para la nueva keychain.

---

## `sign_android_app`

Firma un AAB con `jarsigner`. Para APK no hace nada.

### Parametros

- `artefact_name` (String, **Obligatorio**): nombre del archivo.
- `extension` (String, **Obligatorio**): solo actua si es `aab`.

Copia el artefacto a `unsigned-{nombre}`, borra `META-INF/*`, firma con `SHA256withRSA` / `SHA-256` y, si `jarsigner -verify` pasa, reemplaza el original. Si la verificacion falla, borra la copia y sale con codigo 1.

### Variables de entorno

- `ARTEFACTS_DIR` (opcional): prefijo del path. Vacio usa el directorio actual.
- `KEYSTORE_FILE`, `KEYSTORE_PASS`, `KEY_PASSWORD`, `KEYSTORE_ALIAS`.

No retorna valor.

---

## `sign_android_app_old`

Firma legacy. AAB: `jarsigner` directo y mueve `aligned-{nombre}` sobre el original (el `zipalign` esta comentado). APK: `apksigner sign` a `signed-{nombre}`, verifica y reemplaza el original.

Mismos parametros y variables que `sign_android_app`. No retorna valor.

---

## `is_valid_extension`

Retorna `true` si `extension` es `aab` o `apk`.

---

## `build_app`

Elige el lane de Fastlane y ejecuta `fastlane android {lane}`.

| extension | jarsigner | lane |
|-----------|-----------|------|
| `aab` | `si` | `build_aab` |
| `aab` | otro | `build_sign_release` |
| `apk` | `si` | `build_apk` |
| `apk` | otro | `build_apk_sign_release` |

No retorna valor.

---

## `copy_artifact`

Busca el primer archivo `./app/build/outputs/**/*.{extension}` y lo copia a `${ARTEFACTS_DIR}/{artefact_name}`.

No retorna valor.

---

## `should_upload_to_store`

Retorna `true` solo si `extension` es `aab` y `uploadstore` es `si`.

---

## `upload_to_google_store`

Sube el AAB/APK encontrado en `./app/build/outputs` con `fastlane android upload_google_store track:alpha`. No retorna valor.

---

## `clean_fastlane`

Ejecuta `fastlane android clean`. No retorna valor.

---

## `subir_app_mobsf_old`

Version anterior de la subida a MobSF. Sube `.apk` o `.ipa` a `/api/v1/upload` y sigue el flujo de escaneo legacy. La ruta vigente es `subir_app_mobsf`.

Variables: `MOBSF_HOST_URL`, `MOBSF_AUTH`. No retorna valor. Un fallo de subida de un archivo se loguea y sigue con el siguiente.

---

## `processReport`

Arma un texto con el conteo y el detalle de `appsec` de un JSON de MobSF.

### Parametros

- `reportResponse` (String): JSON del reporte.

### Retorna

String. Por cada categoria lista la cantidad y, si hay hallazgos, titulo y descripcion.

Lo usa `subir_app_mobsf` antes de archivar `{archivo}_informe_appsec_summary_mobsf.txt`.

---

## `enviar_mje_google_chat`

Publica una card en Google Chat con el QR de Diawi.

### Parametros

- `qrCode`: URL del boton "Abrir QR Diawi".
- `appfile`: titulo `Version {appfile}`.
- `extension`: subtitulo de la version subida.

### Variables

- `WEBHOOK_URL`.

No retorna valor. Si el POST falla, loguea el error y no aborta. Lo llama `subir_app_diawi` cuando `ENVIAR_QR` contiene `si`.

---

## `security_codesigning`

Ejecuta `security find-identity -v -p codesigning` y guarda el primer hash de 40 caracteres hex en `env.IDCODESIGNING`.

No retorna valor. Sin identidades, el `.first()` falla.

---

## `obtener_token_api`

Hace login en la API DevOps.

### Variables

- `USER_API_USR`, `USER_API_PSW`
- `API_DEVOPS`: base URL. Endpoint `POST /api/v1/user/login`.

### Retorna

String del token (`user.token`). La password no se imprime (`set +x`).

---

## `llamada_api`

Pide la URL de un artefacto mobile ya publicado.

### Parametros

- `token`: header `Authorization`.
- `extension`, `platform`, `flavor`.

### Variables

- `API_DEVOPS`, `REPO_NEXUS_NAME_DL`, `PACKAGE_NAME`, `VERSIONES`.

Query: `GET /api/v1/version/mob-detail`.

### Retorna

String `url` del JSON. Respuesta vacia o sin `url` aborta.

---

## `clone_react_native_env_repos`

Clona la parametria de React Native, una rama por ambiente, mas `prod`.

### Parametros

- `repoParametriaUrl`: slug del repo en `bitbucket.org/example/{slug}.git`.
- `bitbucketToken`: token de `x-token-auth`.
- `ambientesNoProd` (List): ramas no productivas. Cada una queda en `env_{ambiente}`.

`prod` se clona siempre en `env_prod`. Despues copia el `.env` del primer ambiente de la lista a la raiz. Si ese ambiente tiene `sentry.properties`, lo copia a `android/sentry.properties`.

Sin `.env` en un ambiente, el script sale con codigo 1. No retorna valor.

---

## `switch_env`

Copia el `.env` de un ambiente ya clonado a la raiz, y `sentry.properties` a `android/` si existe.

### Parametros

- `ambiente` (String): nombre del directorio `env_{ambiente}`.

Si no existe el directorio o el `.env`, sale con codigo 1. No retorna valor.