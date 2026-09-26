# menuAndSelectionFunctions

Biblioteca de funciones para presentar menus interactivos y permitir la seleccion de versiones desde diferentes fuentes (Docker, Maven, Git, Nexus).

## Descripcion

Este conjunto de funciones proporciona utilidades para crear menus de seleccion interactivos en pipelines de Jenkins, permitiendo a los usuarios elegir versiones de artefactos desde diferentes repositorios y sistemas de control de versiones.

---

## Funciones Principales

### selectVersionMultiuse

Funcion orquestadora que selecciona una version basandose en el estilo de seleccion proporcionado.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| selectVersionStyle | String | Si | Estilo de seleccion: "docker", "maven", "git", "nexusArtifacts" |
| variables | Map | No | Mapa de variables para el proceso de seleccion (default: [:]) |

#### Estilos de Seleccion Soportados

- **docker**: Llama a `selectVersionDocker`
- **maven**: Llama a `selectVersionMaven`
- **git**: Llama a `selectVersionGit`
- **nexusArtifacts**: Llama a `selectVersionNexus`

#### Retorna

`String` - La version seleccionada.

#### Ejemplo

```groovy
def version = menuAndSelectionFunctions.selectVersionMultiuse('docker', [
    NEXUS_CREDENTIAL: 'nexus-creds',
    NEXUS_URL: 'https://nexus.example.com',
    NEXUS_DOCKER_REPO: 'docker-hosted',
    NEXUS_DOCKER_MICROSERVICE_PATH: 'mi-api',
    COUNT_VERSION: '10'
])
```

---

## Funciones de Seleccion de Versiones

### selectVersionMaven

Selecciona una version de Maven desde un repositorio Nexus mediante la consulta de metadatos.

#### Variables de Entorno Requeridas

- `SERVICE_NAME`: Nombre del servicio/artefacto
- `NEXUS_CREDENTIAL`: ID de credencial para Nexus
- `NEXUS_URL`: URL del servidor Nexus
- `NEXUS_MAVEN_REPO`: Nombre del repositorio Maven
- `NEXUS_MAVEN_GROUPID_WITH_SLASHES`: ID del grupo con slashes (ej: "com/example/app")
- `COUNT_VERSION`: Cantidad de versiones a mostrar

#### Proceso

1. Se conecta al repositorio Maven de Nexus
2. Consulta el archivo `maven-metadata.xml`
3. Extrae las versiones y las ordena por numero de version
4. Presenta un menu de seleccion con las N versiones mas recientes
5. El usuario elige una version con timeout de 60 segundos

#### Ejemplo

```groovy
env.SERVICE_NAME = 'mi-api'
env.NEXUS_CREDENTIAL = 'nexus-creds'
env.NEXUS_URL = 'https://nexus.example.com'
env.NEXUS_MAVEN_REPO = 'releases'
env.NEXUS_MAVEN_GROUPID_WITH_SLASHES = 'com/example/app'
env.COUNT_VERSION = '5'

def selectedVersion = menuAndSelectionFunctions.selectVersionMaven([
    SERVICE_NAME: env.SERVICE_NAME,
    NEXUS_CREDENTIAL: env.NEXUS_CREDENTIAL,
    NEXUS_URL: env.NEXUS_URL,
    NEXUS_MAVEN_REPO: env.NEXUS_MAVEN_REPO,
    NEXUS_MAVEN_GROUPID_WITH_SLASHES: env.NEXUS_MAVEN_GROUPID_WITH_SLASHES,
    COUNT_VERSION: env.COUNT_VERSION
])
```

---

### selectVersionDocker

Selecciona una version de imagen Docker desde un repositorio Docker en Nexus.

#### Variables de Entorno Requeridas

- `NEXUS_CREDENTIAL`: ID de credencial para Nexus
- `NEXUS_URL`: URL del servidor Nexus
- `NEXUS_DOCKER_REPO`: Nombre del repositorio Docker
- `NEXUS_DOCKER_MICROSERVICE_PATH`: Ruta del microservicio en Docker
- `COUNT_VERSION`: Cantidad de versiones a mostrar

#### Proceso

1. Consulta la API REST v1 de Nexus para buscar imagenes Docker
2. Extrae las versiones y las ordena descendentemente
3. Filtra la version "latest" si esta presente
4. Presenta un menu de seleccion con timeout de 360 segundos
5. El usuario selecciona una version

#### Ejemplo

```groovy
def selectedVersion = menuAndSelectionFunctions.selectVersionDocker([
    NEXUS_CREDENTIAL: 'nexus-creds',
    NEXUS_URL: 'https://nexus.example.com',
    NEXUS_DOCKER_REPO: 'docker-hosted',
    NEXUS_DOCKER_MICROSERVICE_PATH: 'mi-api',
    COUNT_VERSION: '10'
])
```

---

### selectVersionGit

Selecciona una version de Git (tags) desde un repositorio Git con credenciales.

#### Variables de Entorno Requeridas

- `GIT_URL`: URL del repositorio Git
- `GIT_CREDENTIAL`: ID de credencial para acceder al repositorio
- `EXPRESSION_FILTER`: Filtro de expresion para tags (ej: "v*", "release-*")
- `COUNT_VERSION`: Cantidad de tags a mostrar

#### Proceso

1. Clona el repositorio Git usando credenciales
2. Obtiene los tags usando `gitFunctions.getTagsCountOnReversePosition`
3. Filtra los tags segun la expresion proporcionada
4. Presenta un menu de seleccion interactivo
5. El usuario elige un tag

#### Ejemplo

```groovy
def selectedVersion = menuAndSelectionFunctions.selectVersionGit([
    GIT_URL: 'https://github.com/example/repo.git',
    GIT_CREDENTIAL: 'github-creds',
    EXPRESSION_FILTER: 'v*',
    COUNT_VERSION: '10'
])
```

---

### selectVersionGitBB

Selecciona versiones de ramas de release desde un repositorio Git (sin credenciales, tipicamente para Bitbucket publico).

#### Variables de Entorno Requeridas

- `GIT_URL`: URL del repositorio Git
- `EXPRESSION_FILTER`: Filtro de expresion para ramas (ej: "release/*")
- `COUNT_VERSION`: Cantidad de ramas a mostrar

#### Proceso

1. Clona el repositorio Git sin credenciales
2. Obtiene ramas de release usando `gitFunctions.getReleaseBranches`
3. Filtra segun el patron proporcionado
4. Presenta un menu de seleccion
5. El usuario elige una rama

#### Ejemplo

```groovy
def selectedBranch = menuAndSelectionFunctions.selectVersionGitBB([
    GIT_URL: 'https://bitbucket.org/example/repo.git',
    EXPRESSION_FILTER: 'release/*',
    COUNT_VERSION: '5'
])
```

---

### selectVersionNexus

Selecciona una version de artefacto desde un repositorio Nexus usando la API REST.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params.nexusCredId | String | Si | ID de credencial para Nexus |
| params.registry | String | Si | Host del servidor Nexus (sin http://) |
| params.repository | String | Si | Ruta del repositorio (group/artifact) |
| params.artifactName | String | Si | Nombre del artefacto |
| params.maxList | Integer | Si | Numero maximo de versiones a mostrar |
| params.regexVersionMatcher | String | No | Expresion regular para extraer version |

#### Retorna

`String` - La version seleccionada. Devuelve lista vacia si hay errores.

#### Proceso

1. Autentica con credenciales de Nexus
2. Consulta la API REST para buscar artefactos
3. Extrae las versiones del nombre de archivo
4. Las ordena en orden descendente (mas recientes primero)
5. Presenta un menu de seleccion
6. Extrae el numero de version usando regex si se proporciona

#### Ejemplo

```groovy
def selectedVersion = menuAndSelectionFunctions.selectVersionNexus([
    nexusCredId: 'nexus-creds',
    registry: 'nexus.example.com:8081',
    repository: 'com/example/myapp',
    artifactName: 'myapp',
    maxList: 10,
    regexVersionMatcher: /.*-(v?\d+\.\d+)\.zip$/
])
```

---

## Funciones Auxiliares

### getVersionNumber

Extrae el numero de version de un nombre de artefacto usando una expresion regular.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| artifactName | String | Si | Nombre del artefacto |
| regex | String | No | Expresion regular personalizada |

#### Expresion Regular por Defecto

```regex
.*-(v?\d+\.\d+)\.zip$
```

Esta expresion coincide con patrones como:
- `myapp-1.0.zip` → extrae `1.0`
- `myapp-v2.5.3.zip` → extrae `v2.5`

#### Retorna

`String` - El numero de version extraido. Retorna `null` si no se encuentra coincidencia.

#### Manejo de Errores

- Captura excepciones durante la extraccion
- Establece `env.MENSAJE` con descripcion del error
- Marca el build como `FAILURE`
- Registra el error en logs

#### Ejemplo

```groovy
def version1 = menuAndSelectionFunctions.getVersionNumber('myapp-1.0.zip')
// Resultado: "1.0"

def version2 = menuAndSelectionFunctions.getVersionNumber(
    'custom-app-v2.5.1.zip',
    /.*-(v?\d+\.\d+\.\d+)\.zip$/
)
// Resultado: "v2.5.1"
```

---

### selectionMenuForStringLines

Muestra un menu de seleccion interactivo para una lista de opciones textuales.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| bunchOfStringLines | String | Si | Texto con lineas separadas por saltos de linea |
| test | Boolean | No | Modo test: muestra opciones sin permitir seleccion (default: false) |

#### Retorna

`String` - La opcion seleccionada. En modo test retorna `null`.

#### Timeout

- 300 segundos (5 minutos) para la seleccion

#### Modo Test

Cuando `test=true`:
- Muestra todas las opciones disponibles
- No permite interaccion del usuario
- util para depuracion y validacion

#### Ejemplo

```groovy
def options = """
v1.0.0
v1.1.0
v2.0.0
v2.1.0
"""

def selected = menuAndSelectionFunctions.selectionMenuForStringLines(options)
// Muestra menu interactivo para seleccionar una version

// Modo test
menuAndSelectionFunctions.selectionMenuForStringLines(options, true)
// Solo lista las opciones sin permitir seleccion
```

---

## Flujo de Datos

### Diagrama de Seleccion de Versiones

```
selectVersionMultiuse()
    ↓
    ├─→ "docker" → selectVersionDocker()
    │                    ↓
    │           Nexus REST API
    │                    ↓
    │           selectionMenuForStringLines()
    │
    ├─→ "maven" → selectVersionMaven()
    │                    ↓
    │           maven-metadata.xml
    │                    ↓
    │           selectionMenuForStringLines()
    │
    ├─→ "git" → selectVersionGit()
    │                    ↓
    │           gitFunctions.getTagsCountOnReversePosition()
    │                    ↓
    │           selectionMenuForStringLines()
    │
    └─→ "nexusArtifacts" → selectVersionNexus()
                                    ↓
                            Nexus REST API
                                    ↓
                            getVersionNumber() [opcional]
                                    ↓
                            selectionMenuForStringLines()
```

---

## Ejemplo Completo de Pipeline

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    stages {
        stage('Select Version - Maven') {
            steps {
                script {
                    env.SELECTED_VERSION = menuAndSelectionFunctions.selectVersionMultiuse('maven', [
                        SERVICE_NAME: 'mi-api',
                        NEXUS_CREDENTIAL: 'nexus-creds',
                        NEXUS_URL: 'https://nexus.example.com',
                        NEXUS_MAVEN_REPO: 'releases',
                        NEXUS_MAVEN_GROUPID_WITH_SLASHES: 'com/example/app',
                        COUNT_VERSION: '10'
                    ])
                    echo "Version seleccionada: ${env.SELECTED_VERSION}"
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo "Desplegando version: ${env.SELECTED_VERSION}"
                }
            }
        }
    }
}
```

---

## Ejemplo con Docker

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    stages {
        stage('Select Docker Image') {
            steps {
                script {
                    env.DOCKER_TAG = menuAndSelectionFunctions.selectVersionMultiuse('docker', [
                        NEXUS_CREDENTIAL: 'nexus-creds',
                        NEXUS_URL: 'https://nexus.example.com',
                        NEXUS_DOCKER_REPO: 'docker-releases',
                        NEXUS_DOCKER_MICROSERVICE_PATH: 'backend-service',
                        COUNT_VERSION: '15'
                    ])
                    echo "Imagen Docker seleccionada: ${env.DOCKER_TAG}"
                }
            }
        }

        stage('Deploy Docker') {
            steps {
                script {
                    sh "docker pull nexus.example.com/backend-service:${env.DOCKER_TAG}"
                    sh "docker run -d nexus.example.com/backend-service:${env.DOCKER_TAG}"
                }
            }
        }
    }
}
```

---

## Ejemplo con Git Tags

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    stages {
        stage('Select Git Release') {
            steps {
                script {
                    env.RELEASE_TAG = menuAndSelectionFunctions.selectVersionMultiuse('git', [
                        GIT_URL: 'https://github.com/myorg/myrepo.git',
                        GIT_CREDENTIAL: 'github-creds',
                        EXPRESSION_FILTER: 'v*',
                        COUNT_VERSION: '20'
                    ])
                    echo "Version seleccionada: ${env.RELEASE_TAG}"
                }
            }
        }

        stage('Checkout and Deploy') {
            steps {
                script {
                    sh "git checkout ${env.RELEASE_TAG}"
                    sh "bash deploy.sh"
                }
            }
        }
    }
}
```

---

## Ejemplo con Nexus Artifacts

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    stages {
        stage('Select Artifact Version') {
            steps {
                script {
                    env.ARTIFACT_VERSION = menuAndSelectionFunctions.selectVersionNexus([
                        nexusCredId: 'nexus-creds',
                        registry: 'nexus.example.com:8081',
                        repository: 'com/mycompany/tools',
                        artifactName: 'deployment-tool',
                        maxList: 15,
                        regexVersionMatcher: /.*-(v?\d+\.\d+\.\d+)\.zip$/
                    ])
                    echo "Version de artefacto seleccionada: ${env.ARTIFACT_VERSION}"
                }
            }
        }

        stage('Download and Execute') {
            steps {
                script {
                    sh """
                        curl -o deployment-tool.zip \\
                            https://nexus.example.com/repository/tools/deployment-tool-${env.ARTIFACT_VERSION}.zip
                        unzip deployment-tool.zip
                        ./deploy.sh
                    """
                }
            }
        }
    }
}
```

---

## Notas Importantes

### Prerequisitos

- Jenkins con acceso a credenciales configuradas
- Acceso a repositorios (Nexus, Git, etc.)
- curl instalado en el agente de Jenkins
- Git instalado (para funciones Git)

### Variables de Entorno

Las credenciales se deben configurar en Jenkins con los IDs correctos:
- `nexus-creds`: Para acceso a Nexus
- `github-creds`: Para acceso a GitHub
- `sonar-credentials`: Para SonarQube

### Timeouts

- **Maven**: 60 segundos
- **Docker**: 360 segundos (6 minutos)
- **Git**: Uso de timeout general de Jenkins
- **Menu de seleccion**: 300 segundos (5 minutos)

### Manejo de Errores

Todas las funciones incluyen:
- Captura de excepciones
- Registros en `env.MENSAJE`
- Fallos explicitos del build en caso de error
- Mensajes descriptivos de error

### Filtros de Expresion

Los filtros de expresion siguen patrones glob:
- `v*` - Tags que comienzan con "v"
- `release/*` - Ramas que comienzan con "release/"
- `*-stable` - Tags que terminan con "-stable"

### Expresiones Regulares

Las expresiones regulares para `getVersionNumber` deben:
- Usar grupos de captura `()` para la version
- El grupo 1 debe contener el numero de version
- Ejemplo: `/.*-(v?\d+\.\d+)\.zip$/` captura "v1.0" o "1.0"

---

## Dependencias

- **gitFunctions**: Para funciones de obtencion de tags y ramas
- **Nexus**: Para acceso a repositorios Maven y Docker
- **Git**: Para operaciones de repositorio
- **curl**: Para consultas HTTP a APIs de Nexus
- **Jenkins Credentials**: Para gestion de credenciales

---

## Troubleshooting

### Error: "Estilo de seleccion de version no reconocido"

**Causa**: El parametro `selectVersionStyle` no es uno de los valores soportados

**Solucion**: Usar uno de estos valores: "docker", "maven", "git", "nexusArtifacts"

### Error: "Empty response from Nexus"

**Causa**: Las credenciales de Nexus son incorrectas o el repositorio no existe

**Solucion**: Verificar credenciales en Jenkins y validar la ruta del repositorio

### Timeout en seleccion de version

**Causa**: El usuario no selecciona una opcion dentro del tiempo limite

**Solucion**: El pipeline fallara, permite reintentar o usar parametros predefinidos

### Version no extraida correctamente

**Causa**: La expresion regular no coincide con el patron del nombre

**Solucion**: Ajustar el parametro `regexVersionMatcher` con el patron correcto

### No hay versiones disponibles

**Causa**: El repositorio no contiene artefactos o el filtro es muy restrictivo

**Solucion**: Verificar el filtro de expresion y la disponibilidad de artefactos en el repositorio

---

**Tags:** `#menu`, `#seleccion`, `#versiones`, `#jenkins`, `#pipeline`, `#nexus`, `#git`, `#docker`, `#maven`, `#interactive`