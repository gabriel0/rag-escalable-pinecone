# Funciones de Despliegue (deployFunctions)

Esta libreria agrupa funciones de utilidad que son comunmente utilizadas durante los flujos de despliegue, como la carga de variables, la manipulacion de versiones y la construccion de nombres de artefactos.

## `loadEnv`

Carga variables de entorno desde archivos de configuracion especificos para una aplicacion y un entorno. Los archivos se buscan en el directorio `env/` del workspace.

### Parametros

- `appName` (String, **Obligatorio**): El nombre de la aplicacion. Se usa para encontrar los archivos de entorno.
- `envName` (String, **Obligatorio**): El nombre del entorno (ej. `develop`, `testing`, `prod`).

### Logica de Ejecucion

1.  Establece las variables de entorno `ENV_NAME` y `MICROSERVICE_NAME`.
2.  Carga el archivo `env/${appName}_global.env`.
3.  Carga el archivo `env/${appName}_${envName}.env`.

> **Nota:** Las variables en archivos cargados posteriormente sobrescriben a las anteriores si tienen el mismo nombre.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Setup') {
    steps {
        script {
            deployFunctions.loadEnv('mi-aplicacion', 'testing')
        }
    }
}
```

---

## `getPomMetadata`

Lee un archivo `pom.xml` de Maven y extrae la version, el `groupId` y el `artifactId`, estableciendolos como variables de entorno.

### Variables de Entorno Requeridas

- `POM_PATH` (String, **Obligatorio**): La ruta al archivo `pom.xml` que se va a leer.

### Variables de Entorno de Salida

- `POM_VERSION`: La version completa del POM (ej. `1.2.3-SNAPSHOT`).
- `GROUPID`: El `groupId` del proyecto.
- `ARTIFACTID`: El `artifactId` del proyecto.
- `VERSION`: La version sin el sufijo `-SNAPSHOT` (ej. `1.2.3`).

---

## `buildVarsForDeploy`

Construye y establece un conjunto de variables de entorno relacionadas con los nombres y tags de las imagenes Docker para los diferentes registros (On-premise y GCP).

### Variables de Entorno Requeridas

- `VERSION`: La version de la aplicacion (ej. `1.2.3`).
- `MICROSERVICE_NAME`: El nombre del microservicio.
- `APIM_NEXUS_DOCKER_URL`, `APIM_NEXUS_DOCKER_DIR`: Configuracion del registro Nexus On-premise.
- `GCP_ARTIFACT_URL`, `GCP_PROJECT`, `GCP_ARTIFACT_NAME`: Configuracion del registro de artefactos de GCP.

### Variables de Entorno de Salida

- `DOCKER_IMAGE_TAG`: El tag de la imagen (ej. `1.2.3`).
- `DOCKER_IMAGE_SINGLE_NAME`: El nombre del microservicio en minusculas.
- `DOCKER_ONPREM_IMAGE_NAME`: La ruta base de la imagen en el registro Nexus.
- `DOCKER_GCP_IMAGE_NAME`: La ruta base de la imagen en el registro de GCP.
- `DOCKER_ONPREM_IMAGE_AND_TAG`: La ruta completa con tag para Nexus.
- `DOCKER_GCP_IMAGE_AND_TAG`: La ruta completa con tag para GCP.

---

## `createAppNewVersion`

Calcula una nueva version para la aplicacion, actualiza el `pom.xml` (si aplica), y crea un nuevo tag en Git para marcar la nueva version de `release` o `hotfix`.

### Parametros

- `aDeployType` (String, **Obligatorio**): El tipo de despliegue.
  - `release`: Incrementa la version menor (ej. `1.2.3` -> `1.3.0`).
  - `hotfix`: Incrementa la version de parche (ej. `1.2.3` -> `1.2.4`).

### Logica de Ejecucion

1.  Calcula la nueva version basandose en la version actual del POM y el `aDeployType`.
2.  Verifica que el tag para la nueva version no exista ya en el repositorio.
3.  Actualiza el archivo `pom.xml` con la nueva version.
4.  Realiza un commit con el cambio en el `pom.xml`.
5.  Crea y empuja un nuevo tag Git (ej. `release-1.3.0`).