# Funciones para librerias Java (Maven y Gradle)

Orquesta compilacion, pruebas y publicacion de librerias Java en Nexus.
Detecta automaticamente el build tool segun el repositorio.

## Estrategia de publicacion

- Commits en `develop`: publican en el repositorio snapshot y exigen version `*-SNAPSHOT`.
- Tags `release-*`: publican en el repositorio retain y exigen version release sin `-SNAPSHOT`.
- El tag `release-x.y.z` debe crearse sobre la rama `releases` o, si esa no existe, `release/x.y.z`.
- Los releases validan que el artefacto no exista previamente en retain para evitar redeploy.

## Deteccion de build tool

| Archivo en raiz | Build tool |
|-----------------|------------|
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |
| Ambos | Error, salvo que `LANGUAGE` indique el tool (`java_mvn` o `java_gradle`) |

`LANGUAGE` de pipelines de servicios tambien se respeta: `java_mvn` / `java_maven` selecciona Maven y `java_gradle` selecciona Gradle.

## Metodos

**materializeBuildFiles**

Copia assets CI segun el build tool detectado:

- Maven: `resources/java/settings.xml`
- Gradle: `resources/java/nexus-init.gradle` + `resources/java/gradle-lib.sh`

**initializeLibEnv**

Configura variables Nexus, metadatos del artefacto e imagen Docker.

- Maven: lee `pom.xml` (`readMavenPom`)
- Gradle: parsea `group` / `version` / `rootProject.name` de `build.gradle(.kts)`

Imagenes Docker:

- Maven: `docker-agents/maven3-jdk:${LANG_VERSION}`
- Gradle: `docker-agents/gradle${GRADLE_MAJOR_VERSION}-jdk:${LANG_VERSION}`

**runPhase**

| Fase pipeline | Maven | Gradle |
|---------------|-------|--------|
| `compile` | `mvn clean compile` | `gradlew classes` |
| `test` | `mvn test` | `gradlew test` |
| `deploy` | `mvn deploy` | `gradlew publish` |

Gradle usa `--init-script nexus-init.gradle` para proxy y publish en Nexus.

Antes de `deploy`, si `env.LIB_PUBLICATION_TYPE` es `release`, se valida que el artefacto no exista ya en el repositorio retain. Si existe, el pipeline aborta con un error controlado indicando que el redeploy no esta permitido y que se debe generar una nueva version/tag release.

Parametros de `runPhase`:

- `phase`: `compile`, `test` o `deploy`.
- `workDir`: default `application`.
- `buildTool`: default `env.BUILD_TOOL` o deteccion por archivos.
- `dockerImage`: default `env.DOCKER_IMAGE`.
- `credentialsId`: default `env.NEXUS_CREDENTIAL_ID`.

Corre como root y monta `${WORKSPACE}/.m2` y `${WORKSPACE}/.gradle`. Al salir restaura el owner del workspace. No retorna valor.

Parametros de `materializeBuildFiles`:

- `targetDir`: default `application`.
- `buildTool`: default `detectBuildTool(targetDir)`.

Parametros de `initializeLibEnv`:

- `workDir`: default `application`.
- `dockerRegistry`: default `env.DOCKERREGISTRY` o `registry.example.com:8083`.
- `buildTool`: default `detectBuildTool(workDir)`.

Exige `LIB_PUBLICATION_TYPE`. Setea `BUILD_TOOL`, metadatos (`ARTIFACT_ID`, `GROUP_ID`, `VERSION`), repos Nexus y `DOCKER_IMAGE`. No retorna valor.

## Metodos de soporte

### detectBuildTool(String workDir)

Retorna `maven` o `gradle`.

Si `LANGUAGE` indica el tool (`java_mvn`, `java_gradle`, `maven`, `gradle`), exige el archivo correspondiente. Si no, usa `pom.xml` o `build.gradle` / `build.gradle.kts`. Los dos a la vez, o ninguno, aborta.

### parseGradleMetadata(String workDir)

Lee `group`, `version` y `rootProject.name` de `build.gradle` (o `.kts`) y `settings.gradle` (o `.kts`).

Retorna `[artifactId, groupId, version]`. Fallbacks: `SERVICE_NAME`, `APP_NAME` y `unspecified`.

### extractGradleProperty(String text, String propertyName)

Busca `propiedad = "valor"`, `val propiedad = "valor"` o `set("propiedad", "valor")`. Retorna el valor o null.

### detectGradleMajorVersion(String workDir)

1. Major de `env.GRADLE_VERSION`.
2. Major de `gradle/wrapper/gradle-wrapper.properties` (`gradle-X.Y.Z-`).
3. `8` si no hay dato.

Retorna el major como string (`8`, no `8.5`).

### configureNexusEnv(String dockerRegistry)

Delega en `libBuildFunctions.configureNexusRepositories('maven')`. El parametro `dockerRegistry` no se usa. No retorna valor.

### mavenArtifactPomUrl()

Arma la URL del POM en retain:

`{LIB_REPOSITORY_URL}{groupId con /}/{artifactId}/{version}/{artifactId}-{version}.pom`

Sin `GROUP_ID`, `ARTIFACT_ID` o `VERSION`, aborta.

### validateMavenRedeployAllowed()

Solo en `LIB_PUBLICATION_TYPE=release`. Si el POM ya responde en Nexus (`NEXUS_CREDENTIAL_ID`), aborta con `abortWithMensaje`. En snapshot no valida. No retorna valor.

### materializeSettings(Map params = [:])

Alias de `materializeBuildFiles`. Lo usa `mavenLibFunctions`.

## Requisitos Gradle en el proyecto

El proyecto debe aplicar el plugin `maven-publish` (o `publishing`) para que la fase `deploy` funcione.

Ejemplo minimo:

```gradle
plugins {
    id 'java-library'
    id 'maven-publish'
}

publishing {
    publications {
        maven(MavenPublication) {
            from components.java
        }
    }
}
```

El init script agrega el repositorio Nexus de publicacion; no hace falta hardcodear URLs en el repo.

## Compatibilidad

`mavenLibFunctions` delega en `javaLibFunctions` (`materializeSettings` -> `materializeBuildFiles`).

## Pipeline consumidor

- `buildLibs.groovy`
