# Funcion para envio de notificaciones a google chat
Funcion para el envio de notificaciones a google chat. Notificaciones respecto al escaneo de trivy, al quality gate de sonar y el pipeline en si mismo.

## Requisitos
La funcion debe recibir una serie de variables, las cuales no son obligatorias. Es decir que si enviamos la variable de sonarQG se enviara una notificacion de sonar, si no la enviamos no habra tal notificacion.
La libreria envia notificaciones en los casos de algun problema, por ejemplo si el QualityGate de sonar termina fallido o si se encuentran vulnerabilidades trivy o si el pipeline termina abortado o fallido, no envia notificaciones cuando el pipeline funciona bien, o cuando no encuentra vulnerabilidades de trivy o cuando el quality gate de sonar es correcto.

## Parametros

    sonarQG: env.sonarQualityGate ?: 'UNKNOWN'

        Si utilizamos la libreria sonarFunctions, esta variable se generara de forma automatica y contendra el estado del QualityGate

    sonarAccessUrl: "${env['SONAR_HOST'] ?: 'UNKNOWN'}/dashboard?id=${env['SONAR_PROJECT_KEY'] ?: 'UNKNOWN'}"

        Esta variable debe contener la ruta al proyecto de SonarQube, en el caso del ejemplo la armamos dinamicamente con los datos de las variables dle proyecto

    trivyLanVuln: env.trivyLanVuln ?: 'UNKNOWN'

        Si utilizamos la libreria trivyFunctions, esta variable se generara de forma automatica y contendra un booleano true/false si se encontraron vulnerabilidades de lenguaje

    trivyOsVuln: env.trivyOsVuln ?: 'UNKNOWN'

        Si utilizamos la libreria trivyFunctions, esta variable se generara de forma automatica y contendra un booleano true/false si se encontraron vulnerabilidades de sistema operativo

    trivyVulnCounts: env.trivyVulnCount ?: 0

        Si utilizamos la libreria trivyFunctions, esta variable se generara de forma automatica y contendra un objeto (lista) con la estadistica de las vulnerabilidades

    buildStatus: currentBuild.currentResult

        Esta variable contiene el estado del pipeline de jenkins

    mensajeSonar: env.MENSAJE_SONAR ?: 'UNKNOWN'

        Si utilizamos la libreria trivyFunctions, esta variable se generara de forma automatica y contendra un booleano true/false si se encontraron vulnerabilidades de lenguaje

    mensajeTrivy: env.MENSAJE_TRIVY ?: 'UNKNOWN'

        Si utilizamos la libreria trivyFunctions, esta variable se generara de forma automatica y contendra un booleano true/false si se encontraron vulnerabilidades de lenguaje

    mensajePipeline: env.MENSAJE ?: 'UNKNOWN'

        En el caso del pipeline unificado, se definio una variable "env.MENSAJE" la cual contiene un error controlado, mediante try/catch de cada step. Entonces dependiende de en que step se produzca la cancelacion esta variable contendra ese mensaje controlado.

    accessUrl: env.BUILD_URL ?: 'UNKNOWN'

        URL del pipeline de jenkins

    webhookUrl: env.WEBHOOKURL ?: 'UNKNOWN'

        WebHook donde enviar esta notificacion

    userName: env.DEPLOY_USER ?: 'UNKNOWN'

        A esta variable se le debera pasar el nombre del usuario que ejecuta el pipeline, basicamente el que invoca el pipeline ya sea de forma manual o por integracion con un trigger de gitlab-jenkins

    aplicacion: env.PROJECT ?: 'UNKNOWN'

        Nombre de la aplicacion, por ejemplo para Fondos Comunes de Inversion sera FCI, para COMEX sera CMXBP, para Transferencias Mep sera TRFMEP

    service: env.SERVICE_NAME ?: 'UNKNOWN'

        Nombre del servicio, por ejemplo fci-consulting-api, cmxbp-bff-support, etc

    version: env.DOCKER_IMAGE_TAG ?: 'UNKNOWN'
        Version del service desplegado

**El UNKNOWN en todos los casos, asignado mediante un ternario cuando se da la condicion, es para evitar enviar variables nulas al metodo**

## Usos

Llamada a la notificaciones desde el bloqueo always de jenkins

```javascript
    post {
        always {
            script {
                notificationsFunctions.sendUnifiedMessage([
                    sonarQG: env.sonarQualityGate ?: 'UNKNOWN',
                    sonarAccessUrl: "${env['SONAR_HOST'] ?: 'UNKNOWN'}/dashboard?id=${env['SONAR_PROJECT_KEY'] ?: 'UNKNOWN'}",
                    trivyLanVuln: env.trivyLanVuln ?: 'UNKNOWN',
                    trivyOsVuln: env.trivyOsVuln ?: 'UNKNOWN',
                    trivyVulnCounts: env.trivyVulnCount ?: 0,
                    buildStatus: currentBuild.currentResult,
                    mensajeSonar: env.MENSAJE_SONAR ?: 'UNKNOWN',
                    mensajeTrivy: env.MENSAJE_TRIVY ?: 'UNKNOWN',
                    mensajePipeline: env.MENSAJE ?: 'UNKNOWN',
                    accessUrl: env.BUILD_URL ?: 'UNKNOWN',
                    webhookUrl: env.WEBHOOKURL ?: 'UNKNOWN',
                    userName: env.DEPLOY_USER ?: 'UNKNOWN',
                    aplicacion: env.PROJECT ?: 'UNKNOWN',
                    service: env.SERVICE_NAME ?: 'UNKNOWN',
                    version: env.DOCKER_IMAGE_TAG ?: 'UNKNOWN'
                ])
            }
        }
    }
```

**Tags:** `#notificaciones`, `#googlechat`