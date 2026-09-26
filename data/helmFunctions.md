# Funcion para orquestacion y/o despliegue relacionado a Helm
- Herramientas de despliegue para charts de helms y generacion de values files

## Parametros
**Metodos principales:**

- installHelmChart: Abstraccion del comando "install" de un chart de helm.
- templateHelmChart: Abstraccion del comando "template" de un chart de helm.
- uninstallHelmChart: Abstraccion del comando "uninstall" de un chart de helm.
- getChartFromGit: Obtiene un chart de helm desde un repo de git.
- getChartFromNexus: Obtiene un chart de helm empaquetado en nexus.
- deployWithChart: Unifica obtencion e instalacion del chart de helm.
- templateWithChart: Unifica obtencion y templating del chart de helm.
- buildConfigManifest: Automatiza la creacion de un manifiesto con los values de helm para la generacion de un configmap.

**Metodos secundarios:**

- aTaskWithChart: Orquestacion de tareas de getChart e installHelmChart/templateHelmChart.
- prepareHelmChartArgs: Prepara y retornar un string predefinido para poder desplegar un chart de helm determinado.
- generateHelmValuesConfigSection: Automatiza la creacion de una seccion de configuracion de configmap para un chart de helm especifico.

## Requisitos
**installHelmChart**

    Requiere los siguientes parametros:

        - aHelmDeployName: Un nombre que identifica el release de helm en k8s.
        - aHelmChart: Un chart o directorio de helm para utilizar en el despliegue.
        - aNamespace: Un namespace de k8s.
        - aStreamOfArgs: Distintos argumentos necesarios para el correcto funcionamiento del chart de helm. 

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**templateHelmChart**

    Requiere los siguientes parametros:

        - aHelmDeployName: Un nombre que identifica el release de helm en k8s.
        - aHelmChart: Un chart o directorio de helm para utilizar en el despliegue.
        - aStreamOfArgs: Distintos argumentos necesarios para el correcto funcionamiento del chart de helm. 

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**uninstallHelmChart**

    Requiere los siguientes parametros:

        - aHelmDeployName: Un nombre que identifica el release de helm en k8s.
        - aNamespace: Un namespace de k8s.

    Requiere las siguientes variables de entorno: SERVICE_CREDS, CLUSTER_NAME, AWS_REGION.

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**getChartFromGit**

    Requiere los siguientes parametros:

        - aHelmChartGitRepo: Una url de repo de git.
        - gitCommitReference: Un commit de referencia de donde tomar el chart. En la mayoria de los casos una branch o un tag.
        - aGitRepoCredential: Una credencial para el acceso al repo de git.

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**getChartFromNexus**

    Requiere los siguientes parametros:

        - aHelmRegistryUrl: Una url de nexus de un repo en formato helm.
        - aHelmChartName: El nombre del chart de helm en el repo de nexus.
        - aHelmChartVersion: La version del chart de helm.
        - aNexusRepoCredential: Una credencial para el acceso a nexus. 

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**aTaskWithChart**

    Requiere los siguientes parametros:

        - aHelmChartTask: Comando de helm "install" o "template".
        - ahelmChartLocation: Origen del chart de helm, puede ser git o nexus.
        - aHelmChartName: Nombre del chart de helm.
        - aHelmChartVersion: Version del chart de helm.
        - aHelmChartArgs: Distintos argumentos necesarios para el correcto funcionamiento del chart de helm. 

    Requiere las siguientes variables de entorno: HELM_CHART_GIT_REPO(Solo chart git), CREDENTIAL_GIT(Solo chart git), HELM_CHART_REGISTRY_URL(Solo chart nexus), NEXUS_CREDENTIAL_ID(Solo chart nexus), SERVICE_CREDS, CLUSTER_NAME, AWS_REGION, SERVICE_NAME, NAMESPACE.

    Respuesta:

        No retorna ningun valor. Solo el output del commando por stdout.

**buildConfigManifest**

    Requiere los siguientes parametros:

        - manifestDestination: Ruta donde quedara el manifiesto generado.
        - baseManifest: Manifiesto base para la generacion del manifiesto, contiene la estructura obligada del yaml.
        - configsList: Una lista de mapas/objetos con la siguiente estructura.
                      - configMapName: Nombre del configmap a generar.
                      - fileList: Lista de mapas/objetos con la siguiente estructura.
                                - name: Nombre que tendra el archivo sobre la definicion del configmap.
                                - path: Path del archivo de configuracion crudo (En formato que utiliza la app)

    Respuesta:

        Retorna la ruta del manifiesto generado.

## Ejemplos de uso
Llamada a los metodos

```javascript

        stage("Kubernetes -- Despliegue") {
            steps {
                script {
                    env.SERVICE_NAME = "microservice-name"
                    env.NAMESPACE = "microservice-namespace"
                    env.HELM_CHART_NAME = "un-chart"
                    env.HELM_CHART_VERSION = "1.0.0"
                    env.HELM_CHART_SOURCE = "nexusRepo"
                    env.HELM_CHART_GIT_REPO = "git@git.example.com:helm-charts.git"
                    env.CREDENTIAL_GIT = "some-git-credential"
                    env.HELM_CHART_REGISTRY_URL = "http://registry.example.com:8081/repository/helm-repo"
                    env.NEXUS_CREDENTIAL_ID = "some-nexus-credential"
                    env.SERVICE_CREDS = "some-aws-credential"
                    env.CLUSTER_NAME = "demo-eks-cluster"
                    env.AWS_REGION = "us-east-1"

                    dir("configs") {
                        chartArgs = helmFunctions.prepareHelmChartArgs(HELM_CHART_NAME)
                        if (  params.k8sDeployType == "install" ) {
                            helmFunctions.deployWithChart(HELM_CHART_SOURCE, HELM_CHART_NAME, HELM_CHART_VERSION, chartArgs)
                        } else if ( params.k8sDeployType == "template" ) {
                            helmFunctions.templateWithChart(HELM_CHART_SOURCE, HELM_CHART_NAME, HELM_CHART_VERSION, chartArgs)
                        } else if ( params.k8sDeployType == "uninstall" ) {
                            helmFunctions.uninstallHelmChart(SERVICE_NAME, NAMESPACE)
                        } else {
                            echo("Comando Helm no reconocido")
                        }
                    }
                }
            }
        }

        stage("Config -- Build") {
            steps {
                script {
                    def globalConfigMapParams = [
                        configMapName: "targets",
                        filesList: [
                            [name: "targets.yaml", path: "configuration/global/${ENVIRONMENT}/targets.yaml"],
                        ]
                    ]
                    def microserviceConfigMapParams = [
                        configMapName: "${SERVICE_NAME}-config",
                        filesList: [
                            [name: "config.yaml", path: "application/config/config-${ENVIRONMENT}.yaml"],
                        ]
                    ]
                    def configParamStructure = [
                        [manifestDestination: "pipeline/configs/${PROJECT}/${ENVIRONMENT}/${SERVICE_NAME}/automated_services_values.yaml",
                        baseManifest: "baseMicroserviceManifest.yaml",
                        configsList: [microserviceConfigMapParams]
                        ],
                        [manifestDestination: "pipeline/global_shared/${ENVIRONMENT}/automated_global_shared_values.yaml",
                        baseManifest: "baseGlobalManifest.yaml",
                        configsList: [globalConfigMapParams]
                        ]
                    ]
                    try {
                        sh("/bin/bash base/scripts/apimConfigBaseValues.sh") // Genera los baseManifest necesarios
                        configParamStructure.each{ aConfigParam ->
                            buildConfigManifest(aConfigParam)
                        }
                    } catch (Exception e) {
                        env.MENSAJE = "Pipeline: Error construyendo configuraciones"
                        println "${env.MENSAJE}"
                        error("${e.message}")
                    }
                }
            }
        }
```
**Tags:** `#helm`, `#manifiestos`, `#values`