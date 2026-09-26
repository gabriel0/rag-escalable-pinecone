# Funcion para escaneo de vulnerabilidades con trivy
- Escaneo de vulnerabilidades de Sistema Operativo y/o Lenguaje

## Informacion

- Se utiliza la imagen "registry.example.com:8083/docker-agents/trivy:pipeline-test" o "registry.example.com:8083/docker-agents/trivy:pipeline"
    * "pipeline" se utiliza en los pipelines productivos
    * pipeline-test se utiliza en los pipelines de prueba.

*La idea es probar las imagenes a medida que se liberan utilizando el job de construccion: [pipe_construccion_docker](https://jenkins.example.com:8443/view/Mantenimiento/job/Devops/job/MANTENIMIENTO/job/DOCKER/job/dockerBuild/). Por ejemplo al momento de escribir este documento la imagen copn la cual se contruyo es 0.61.0 y eso esta indicado en el changelog del repositorio de docker-build*

[CHANGELOG](http://git.example.com:9999/ALM/maintenance/docker-build/-/blob/main/trivy/changelog.md?ref_type=heads)

*Una vez que se homologue la nueva version de trivy, por ejemplo la 0.62.0, se podra construir la imagen y subirla a nexus como pipeline para ser utilizada por los pipelines productivos*

## Parametros
**Metodos principales:**

- call: Metodo orquestador, hace todo lo que hace imageScanner + mainTrivy en un metodo unificado.

- imageScanner: Ejecuta un analisis de vulnerabilidades y devuelve un resultado (string) con el resumen de las mismas. Este metodo invoca a los metodos secundarios _downloadTrivyIgnore y _processResult.

- mainTrivy: Toma el resultado del proceso imageScanner (reportetrivy.json), con este ejecuta los siguientes metodos segundarios _countVulnerabilities, _langVulnerabilities, _osVulnerabilities. El resultado de esta funcion es un mapa de datos con el resumen de las vulnerabilidades.

**Metodos secundarios:**

- _downloadTrivyIgnore: Si existe descarga el archivo de exclusiones y devuelve un booleano.

- _processResult: Toma el resultado del analisis de vulnerabilidades y genera un reporte del tipo resumen (string), utilizando los metodos _getResultResume y _processVulnerabilities.

- _processVulnerabilities:

- _getResultResume:

- _countVulnerabilities: Toma el resultado del analisis de vulnerabilidades (.json) y se arma un mapa con el resumen de vulnerabilidades por criticidad y tipo.

- _checkVulnerabilities: Es un metodo invocado por _langVulnerabilities y _osVulnerabilities, para validar si existen vulnerabilidades del tipo, devolviendo un booleano. Tambien tiene la capacidad de cancelar un pipeline, mediante el uso de una parametro "ABORT_ON_TRIVY" en 1.

- _langVulnerabilities: Invoca el metodo _checkVulnerabilities, indicandole que busque vulnerabilidades de lenguaje y devuelve un booleano true/false.

- _osVulnerabilities: Invoca el metodo _checkVulnerabilities, indicandole que busque vulnerabilidades de sistema operativo y devuelve un booleano true/false.

## Requisitos
**imageScanner**

    Requiere los siguientes parametros:

        - imageName: Nombre de la imagen a escanear.
        - imageVersion: Version de imagen a escanear.
        - trivyPath: En el caso que queramos escanear el codigo aplicativo, debemos pasar la ruta donde descargamos el codigo.
        - trivyIgnoreUrlPath: Se debe pasar el url path de nexus, del proyecto, el cual contendra el archivo de exclusiones. En caso que el path no exista o no contenga el archivo de exclusiones, no lo utilizara.
        - ignoreUnfix: Parametro alternativo, no obligatorio, el cual puede ser false (por defecto) o true
        - severities: Parametro alternativo, no obligatorio, el cual puede ser CRITICAL,HIGH,MEDIUM,INFO etc en todas sus combinaciones. Este parametro se utiliza para determinar que tipo de vulnerabilidades escanear, por defecto es "CRITICAL,HIGH"
        - scanTypes: Parametro alternativo, no obligatorio, el cual puede ser "os,lang" "os" "lang". Este parametro se utiliza para definir que tipo de vulnerabilidades escanear, por defecto es "os,lang".

    Respuesta:

        Devuelve un reporte de vulnerabilidades:

        ArtifactName: registry.example.com:8099/repository/fci/fci-consulting-api:devops
        ArtifactType: container_image
        CreateDate: 2024-09-17T19:08:38.352412284Z


**mainTrivy**

    Requiere los siguientes parametros:

        - trivyPath: En el caso que queramos escanear el codigo aplicativo, debemos pasar la ruta donde descargamos el codigo.
        - abortOnVuln: Si pasamos un valor en 1, se puede hacer cancelar el pipeline en caso que se hayen vulnerabilidades definidas en abortStrSeverities
        - abortStrSeverities: Listado separado por comas de vulnerabilidades con las cuales cancelar el pipeline (CRITICAL,HIGH)

    Respuesta:

        Devuelve un mapa de datos sobre las vulnerabilidades por criticidad / tipo. Tambien define dos variables del tipo environment, las cuales contendran un true/false sobre si se encontraron o no vulnerabilidades de lenguaje y/o sistema operativo. Estas variables son utilizadas por la libreria de notificaciones (env.trivyLanVuln y env.trivyOsVuln)

        Critical: total=1, osPkgs=1, langPkgs=0
        High: total=8, osPkgs=7, langPkgs=1
        Medium: total=1, osPkgs=0, langPkgs=1
        Other: total=0, osPkgs=0, langPkgs=0

**call**

    Requiere los siguientes parametros:

        - imageName: Nombre de la imagen a escanear.
        - imageVersion: Version de imagen a escanear.
        - trivyPath: En el caso que queramos escanear el codigo aplicativo, debemos pasar la ruta donde descargamos el codigo.
        - trivyIgnoreUrlPath: Se debe pasar el url path de nexus, del proyecto, el cual contendra el archivo de exclusiones. En caso que el path no exista o no contenga el archivo de exclusiones, no lo utilizara.
        - ignoreUnfix: Parametro alternativo, no obligatorio, el cual puede ser false (por defecto) o true
        - severities: Parametro alternativo, no obligatorio, el cual puede ser CRITICAL,HIGH,MEDIUM,INFO etc en todas sus combinaciones. Este parametro se utiliza para determinar que tipo de vulnerabilidades escanear, por defecto es "CRITICAL,HIGH"
        - abortOnVuln: Parametro alternativo, no obligatorio, si pasamos valor 1, se puede hacer cancelar el pipeline en caso que se hayen vulnerabilidades definidas en abortStrSeverities
        - abortStrSeverities: Parametro alternativo, no obligatorio, listado separado por comas de vulnerabilidades con las cuales cancelar el pipeline (CRITICAL,HIGH)

## Ejemplos de uso
Llamada a los metodos

***Con metodos individuales***
```javascript
        stage("ContainerImage -- ScanTrivy") {
            steps {
                withCredentials([usernamePassword(credentialsId : env.NEXUS_CREDENTIAL_ID,usernameVariable: 'nexusUser', passwordVariable: 'nexusPassword')]){
                    script {
                        dir("application"){
                            def TRIVY_IMAGE_NAME="${env.NEXUS_DOCKER_HOST}/${env.NEXUS_DOCKER_REPOSITORY}/${env.CONTAINER_IMAGE_NAME}"
                            def TRIVY_IMAGE_VERSION="${env.CONTAINER_IMAGE_TAG}"
                            def TRIVY_PATH=pwd()
                            def TRIVY_IGNORE_URLPATH="${env.ENVIRONMENT}/${env.APP_NAME}/${env.SERVICE_NAME}"
                            trivyFunctions.imageScanner(TRIVY_IMAGE_NAME, TRIVY_IMAGE_VERSION, TRIVY_PATH, TRIVY_IGNORE_URLPATH, env?.TRIVY_IGNORE_UNFIXED, env?.TRIVY_SEVERITY)
                            trivyFunctions.mainTrivy(TRIVY_PATH, env?.ABORT_ON_TRIVY, env?.ABORT_TRIVY_SEV)
                        }
                    }
                }
            }
        }
```
***Con metodo orquestador (call)***
```javascript
        stage("ContainerImage -- ScanTrivy") {
            steps {
                withCredentials([usernamePassword(credentialsId : env.NEXUS_CREDENTIAL_ID,usernameVariable: 'nexusUser', passwordVariable: 'nexusPassword')]){
                    script {
                        dir("application"){
                            def trivyParams = [
                                imageName: "${env.NEXUS_DOCKER_HOST}/${env.NEXUS_DOCKER_REPOSITORY}/${env.CONTAINER_IMAGE_NAME}",
                                imageVersion: "${env.CONTAINER_IMAGE_TAG}",
                                trivyPath: pwd(),
                                trivyIgnoreUrlPath: "${env.ENVIRONMENT}/${env.APP_NAME}/${env.SERVICE_NAME}",
                                ignoreUnfix: env?.TRIVY_IGNORE_UNFIXED,
                                severities: env?.TRIVY_SEVERITY,
                                abortOnVuln: env?.ABORT_ON_TRIVY,
                                abortStrSeverities: env?.ABORT_TRIVY_SEV
                            ]
                            trivyFunctions(trivyParams)
                        }
                    }
                }
            }
        }
```

**Tags:** `#trivy`, `#vulnerabilidades`