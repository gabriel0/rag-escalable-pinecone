# Construccion de codigo (buildCodeFunctions)

Compila aplicaciones y prepara los argumentos de build Docker a partir del tipo de proyecto detectado en el workspace.

## `buildApp`

Enruta la compilacion segun el lenguaje.

### Parametros

- `anAppLanguage` (String, **Obligatorio**): lenguaje a construir. Valor soportado: `java`.

### Respuesta

No retorna valor. Delega en `buildJavaAppV1`.

Si el lenguaje no es `java`, setea `env.MENSAJE` a `Error en build, no se pudo reconocer el lenguaje` y aborta con `error`.

### Ejemplo

```groovy
buildCodeFunctions.buildApp('java')
```

---

## `buildJavaAppV1`

Ejecuta `docker build` de una aplicacion Java usando el Dockerfile del workspace. Etiqueta la imagen para el registro on-prem y para el registro cloud.

### Parametros

No recibe argumentos. Lee variables de entorno.

### Variables de entorno

- `NEXUS_CREDENTIAL_ID` (**Obligatorio**): credencial Jenkins `usernamePassword` de Nexus.
- `LANG_VERSION`, `CONTAINERPORT1`, `RUN_TESTS`, `NEXUS_PROXY_HOST`, `NEXUS_PROXY_REPOSITORY`.
- `SERVICE_NAME`, `BUILD_NUMBER`, `DOCKERFILE`.
- `DOCKER_DEPLOY_ONPREM_IMAGE`, `DOCKER_DEPLOY_CLOUD_IMAGE`, `DOCKER_IMAGE_TAG`.

Build args fijos: `IMAGE_REGISTRY=registry.example.com:8083`, `APP_SRC=src`. Usa `--no-cache`.

### Respuesta

No retorna valor. Ante excepcion setea `MENSAJE=Problemas buildJavaApp`, marca el build como `FAILURE` y relanza el error.

---

## `getBuildData`

Detecta el tipo de proyecto en la raiz del workspace y carga variables de entorno para el build. Escribe `docker_build.args`.

Prioridad de deteccion: `pom.xml`, luego `gradle.properties`, luego `package.json`.

### Parametros

Ninguno.

### Variables que escribe

Comunes a los tres tipos:

- `LANGUAGE`: `JAVA` (Maven/Gradle) o `JS`.
- `APP_VERSION`: version leida del proyecto.
- `DOCKER_IMAGE_TAG`: `latest` si `ENVIRONMENT=dev`; si no, `APP_VERSION`.

Solo Java:

- `ARTIFACTID_NEXUS`
- `JAVA_FILE` (`{artifactId}.jar`)

Segun el tipo:

| Archivo | Extra |
|---------|--------|
| `pom.xml` | `POM_PATH`, version y artifactId via `readMavenPom`. Args: `MAVEN_PUBLIC_REPOSITORY`, `JAVA_FILE`, `NEXUS_REPOSITORY_ID`. |
| `gradle.properties` | `rootProject.name` desde `settings.gradle`. Version desde `utilsFunctions.readVersionsToml()` (`project`) o, si no hay, `version` de `gradle.properties`. Args de snapshots, releases, Maven publico y `GRADLE_DISTRIBUTION_REPO`. |
| `package.json` | `PKG_PATH`. Version con `grep` de `"version"`. Arg `BASE64_TOKEN`. |

`docker_build.args` siempre incluye `ENVIRONMENT`, hosts y credenciales de Nexus, datos de Sonar y `GIT_REPO` / `GIT_APP_BRANCH`.

### Respuesta

No retorna valor. Si no existe ninguno de los tres archivos, aborta con `No se detecto tipo de proyecto valido`.

### Ejemplo

```groovy
buildCodeFunctions.getBuildData()
echo "Lenguaje ${env.LANGUAGE}, tag ${env.DOCKER_IMAGE_TAG}"
```

**Tags:** `#build`, `#java`, `#docker`
