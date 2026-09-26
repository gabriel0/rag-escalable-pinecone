# Funcion para tareas de sonarqube
- Escaneos (QualityGates)
- TAG de proyectos
- Creacion de proyectos
- Obtencion de metricas de resultado de escaneos

## Parametros
**Metodos:**

- Metodo fetchOverallMetrics: Listara las metricas del Overall del codigo de SonarQube

    ***El codigo overall, son las lineas acumuladas de codigo, es decir el 100% del codigo analizado por todos los escaneos de Sonar***

- Metodo fetchNewMetrics: Listara las metricas del codigo reciente reportado a SonarQube

    ***El codigo new, son las nuevas lineas de codigo analizadas en el ultimo escaneo de Sonar***

- Metodo checkAndHandleQualityGate: Devuelve el estado del QualityGate OK/ERROR, tambien tiene la capacidad de cancelar el pipeline si se declara una variable y se pasa como parametro con el contenido "1"

## Requisitos
**fetchOverallMetrics**

    Requiere los siguientes parametros:

        - sonarHost: URL del nodo sonar http://sonar.example.com:9200
        - projectKey: Normalmente el nombre del proyecto en sonar, que debe representar el service_name (nombre del servicio)
        - sonarToken: Token de sonar con, al menos, permisos de lectura del proyecto

    Respuesta:

        Responde con un objeto map key=value, conteniendo las metricas y su resultado

        Overall Code Metrics:
        code_smells: 192
        vulnerabilities: 0
        alert_status: ERROR
        coverage: 0.0
        bugs: 0
        duplicated_lines_density: 1.9

**fetchNewMetrics**

    Requiere los siguientes parametros:

        - sonarHost: URL del nodo sonar http://sonar.example.com:9200
        - projectKey: Normalmente el nombre del proyecto en sonar, que debe representar el service_name (nombre del servicio)
        - sonarToken: Token de sonar con, al menos, permisos de lectura del proyecto

    Respuesta:

        Responde con un objeto map key=value, conteniendo las metricas y su resultado:

        New Code Metrics:
        New_duplicated_lines_densityStatus: OK
        New_duplicated_lines_densityValue: 0.0
        New_violationsStatus: ERROR
        New_violationsValue: 12


**checkAndHandleQualityGate**

    Requiere los siguientes parametros:

        - sonarHost: URL del nodo sonar http://sonar.example.com:9200
        - projectKey: Normalmente el nombre del proyecto en sonar, que debe representar el service_name (nombre del servicio)
        - sonarToken: Token de sonar con, al menos, permisos de lectura del proyecto
        - abortQG: Esta variable, por defecto es 0, si se envia 1 el pipeline cancelara si el qualitygate termino en error. La estrategia ideal es que el servicio tenga una variable de ambiente env.ABORT_ON_QG la cual contenga el valor deseado y sea enviada como parametro en el pipeline a este metodo, asi si en algun momento se decide cancelar el pipeline de determinados servicios con tan solo cambiar la declaracion de la variable sucedera.

    Respuesta:

        Si la variable abortQG es 1 y falla el Quality;
            Sonarqube: quality gate "NOMBRE DEL SERVICIO" en estado: ERROR, se cancela el pipeline
        Si la variable abortQG es 0/1 y no falla el Quality;
            Sonarqube: quality gate "NOMBRE DEL SERVICIO" en estado: OK
        Si la variable abortQG es 0 y falla el Quality;
            Sonarqube: quality gate "NOMBRE DEL SERVICIO" en estado: ERROR

## Ejemplos de uso

### Ejemplos de uso funcion mainSonarDocker
Esta alternativa de uso es teniendo en cuenta que el escaneo de sonar y su resultado ya fueron subidos, por ejemplo usando un dockerfile (pipeline unificado) durante el proceso de build+coverage de la aplicacion.

- sonarHost La URL del servidor SonarQube, esta variable se traduce como el parametro -Dsonar.host.url""
- projectKey La clave del proyecto en SonarQube, esta variable se traduce como el parametro -Dsonar.projectKey=""
- projectName El nombre del proyecto a crear, esta variable se traduce como el parametro -Dsonar.projectName=""
- sonarToken El token de autenticacion para SonarQube, esta variable se traduce como el parametro -Dsonar.token=""
- sonarTag: Es utilizado para crear un tag en Sonar, este tag es de ayuda a la hora de ordenar los servicios a un nivel jerarquico por aplicacion/solucion
- abortQG: Es utilizado para determinar si se debe o no abortar el pipeline cuando el QualityGate esta en estado ERROR

```javascript
        stage("Application -- SonarQube") {
            steps {
                script {
                    docker.image("${env.DOCKER_PIPELINE_RUN}/${env.DOCKER_PIPELINE_IMAGE}").inside(" --entrypoint=''  ") {
                        withCredentials([usernamePassword(credentialsId: env.SONAR_LOGIN, usernameVariable: 'SONAR_LOGIN',passwordVariable: 'SONAR_TOKEN')]) {
                            try {
                                sonarFunctions.mainSonarDocker(
                                    sonarHost: env.SONAR_HOST,
                                    projectKey: env.SERVICE_NAME,
                                    projectName: env.SERVICE_NAME,
                                    sonarToken: env.SONAR_TOKEN,
                                    sonarTag: env.PROJECT,
                                    abortQG: env?.ABORT_ON_QG
                                )
                            } catch (Exception e) {
                                env.MENSAJE = "Pipeline: Problemas para obtener metricas de SonarQube"
                                println MENSAJE
                                error("${e.message}")
                            }
                        }
                    }
                }
            }
        }
```

### Ejemplos de uso funcion mainSonar
Este metodo es valido cuando no utilizamos la estrategia de DockerFile para realizar el build+coverage, es decir que necesitamos lanzar el sonar-scanner directamente en el codigo descargado sin estrategias de dockerfile.

- sonarHost La URL del servidor SonarQube, esta variable se traduce como el parametro -Dsonar.host.url""
- projectKey La clave del proyecto en SonarQube, esta variable se traduce como el parametro -Dsonar.projectKey=""
- projectName El nombre del proyecto a crear, esta variable se traduce como el parametro -Dsonar.projectName=""
- sonarToken El token de autenticacion para SonarQube, esta variable se traduce como el parametro -Dsonar.token=""
- sourcesDir El directorio de las fuentes a escanear, esta variable se traduce como el parametro -Dsonar.sources=""
- appVersion Version del codigo, esta variable se traduce como el parametro -Dsonar.projectVersion=""
- additionalProps:
    Mapa de parametros adicionales, se puede enviar cualquier parametro a sonar-scanner.
    Los cuales seran agregados al comando de sonar-scanner como -D${parametro} -D${parametro2}, asi tantas veces como additionalProps enviemos separados por coma.
- sonarTag: Es utilizado para crear un tag en Sonar, este tag es de ayuda a la hora de ordenar los servicios a un nivel jerarquico por aplicacion/solucion
- abortQG: Es utilizado para determinar si se debe o no abortar el pipeline cuando el QualityGate esta en estado ERROR

Ejemplo java maven:

***Requisito: haber corrido el build (y opcionalmente `mvn dependency:copy-dependencies`) para que existan `target/classes` y los JARs en `target/dependency/`.***
***Sin `sonar.java.libraries`, SonarQube avisa que el analisis de fuentes Java sera menos preciso.***

```javascript
stage("Application -- SonarQube") {
    steps {
        script {
            def sonarImageRegistry = env.DOCKER_PIPELINE_RUN?.trim()
            docker.image("${sonarImageRegistry}/docker-agents/sonar-scanner-cli:5.0.1").inside(" --entrypoint=''  ") {
                withCredentials([usernamePassword(
                    credentialsId: env.SONAR_LOGIN,
                    usernameVariable: 'SONAR_LOGIN',
                    passwordVariable: 'SONAR_TOKEN'
                )]) {
                    dir('application') {
                        sonarFunctions.mainSonar(
                            sonarHost: env.SONAR_HOST,
                            projectKey: env.SERVICE_NAME,
                            projectName: env.SERVICE_NAME,
                            sonarToken: env.SONAR_TOKEN,
                            sonarTag: env.APP_NAME,
                            appVersion: env.APP_VERSION,
                            sourcesDir: "src",
                            abortQG: "0",
                            additionalProps: [
                                "sonar.java.source": "11",
                                "sonar.java.binaries": "target/classes",
                                "sonar.java.libraries": "target/dependency/*.jar"
                            ]
                        )
                    }
                }
            }
        }
    }
}
```

Ejemplo java gradle:

***Requisito: haber corrido el build y copiado las dependencias (p. ej. a `build/dependency/`) para que existan las clases y los JARs.***
***Sin `sonar.java.libraries`, SonarQube avisa que el analisis de fuentes Java sera menos preciso.***
***Nota: `build/libs/*.jar` suele contener solo el artefacto del proyecto; las dependencias deben apuntarse por separado.***

```javascript
stage("Application -- SonarQube") {
    steps {
        script {
            def sonarImageRegistry = env.DOCKER_PIPELINE_RUN?.trim()
            docker.image("${sonarImageRegistry}/docker-agents/sonar-scanner-cli:5.0.1").inside(" --entrypoint=''  ") {
                withCredentials([usernamePassword(
                    credentialsId: env.SONAR_LOGIN,
                    usernameVariable: 'SONAR_LOGIN',
                    passwordVariable: 'SONAR_TOKEN'
                )]) {
                    dir('application') {
                        sonarFunctions.mainSonar(
                            sonarHost: env.SONAR_HOST,
                            projectKey: env.SERVICE_NAME,
                            projectName: env.SERVICE_NAME,
                            sonarToken: env.SONAR_TOKEN,
                            sonarTag: env.APP_NAME,
                            appVersion: env.APP_VERSION,
                            sourcesDir: "src",
                            abortQG: "0",
                            additionalProps: [
                                "sonar.java.source": "11",
                                "sonar.java.binaries": "build/classes/java/main",
                                "sonar.java.libraries": "build/dependency/*.jar"
                            ]
                        )
                    }
                }
            }
        }
    }
}
```

Ejemplo nodejs:

```javascript
stage("Application -- SonarQube") {
    steps {
        script {
            def sonarImageRegistry = env.DOCKER_PIPELINE_RUN?.trim()
            docker.image("${sonarImageRegistry}/docker-agents/sonar-scanner-cli:5.0.1").inside(" --entrypoint=''  ") {
                withCredentials([usernamePassword(
                    credentialsId: env.SONAR_LOGIN,
                    usernameVariable: 'SONAR_LOGIN',
                    passwordVariable: 'SONAR_TOKEN'
                )]) {
                    dir('application') {
                        sonarFunctions.mainSonar(
                            sonarHost: env.SONAR_HOST,
                            projectKey: env.SERVICE_NAME,
                            projectName: env.SERVICE_NAME,
                            sonarToken: env.SONAR_TOKEN,
                            sonarTag: env.APP_NAME,
                            appVersion: env.APP_VERSION,
                            sourcesDir: "src",
                            abortQG: "0",
                            additionalProps: [
                                "sonar.javascript.lcov.reportPaths": "coverage/lcov.info"
                            ]
                        )
                    }
                }
            }
        }
    }
}
```

Ejemplo python:

```javascript
stage("Application -- SonarQube") {
    steps {
        script {
            def sonarImageRegistry = env.DOCKER_PIPELINE_RUN?.trim()
            docker.image("${sonarImageRegistry}/docker-agents/sonar-scanner-cli:5.0.1").inside(" --entrypoint=''  ") {
                withCredentials([usernamePassword(
                    credentialsId: env.SONAR_LOGIN,
                    usernameVariable: 'SONAR_LOGIN',
                    passwordVariable: 'SONAR_TOKEN'
                )]) {
                    dir('application') {
                        sonarFunctions.mainSonar(
                            sonarHost: env.SONAR_HOST,
                            projectKey: env.SERVICE_NAME,
                            projectName: env.SERVICE_NAME,
                            sonarToken: env.SONAR_TOKEN,
                            sonarTag: env.APP_NAME,
                            appVersion: env.APP_VERSION,
                            sourcesDir: ".",
                            abortQG: "0",
                            additionalProps: [
                                "sonar.python.coverage.reportPaths": "coverage.xml"
                            ]
                        )
                    }
                }
            }
        }
    }
}
```

## Exclusiones sonar

### Estrategia dockerfile (pipeline unificado)

- Metodo: mainSonarDocker

    Se debe crear un sonar-project.properties en la raiz del repositorio con el siguiente formato de contenido:
```
sonar.exclusions=\
  src/main/java/com/example/support/config/**,\
  src/main/java/com/example/support/exception/**,\
  src/main/java/com/example/support/models/**
```
***Este archivo es levantado por el DockerFile del pipeline unificado y utilizado comom exclusion.***

### Estrategia sin dockerfile

- Metodo: mainSonar

    Se debe crear un sonar-project.properties en la raiz del repositorio con el siguiente formato de contenido:
```
sonar.exclusions=\
  src/main/java/com/example/support/config/**,\
  src/main/java/com/example/support/exception/**,\
  src/main/java/com/example/support/models/**
```

***Este archivo sera levantado por el proceso de sonar-scanner, siempre y cuando se encuentre en la raiz, para las exclusiones por el metodo mainSonar***

**Tags:** `#sonarqube`, `#sonar`, `#quality`, `#gate`