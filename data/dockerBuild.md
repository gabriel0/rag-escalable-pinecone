# dockerBuild

Biblioteca de funciones para construir imagenes Docker en pipelines de Jenkins.

## Descripcion

Este conjunto de funciones proporciona utilidades para construir imagenes Docker con diferentes estrategias, gestionar registros (Nexus y ECR), realizar login a registries y ejecutar analisis de cobertura de codigo con SonarQube.

---

## Funciones

### generateTags

Genera las etiquetas para las imagenes Docker basadas en los parametros proporcionados.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros que incluye informacion sobre los registros de Docker y las configuraciones de etiquetas |
| params.nexusDockerHost | String | No | Host del registro Docker de Nexus (ej: "nexus.example.com:8082") |
| params.nexusDockerRepository | String | Condicional | Repositorio de Nexus (requerido si nexusDockerHost esta presente) |
| params.ecrRegistry | String | No | URL del registro ECR de AWS |
| params.ecrRepository | String | Condicional | Repositorio de ECR (requerido si ecrRegistry esta presente) |
| params.dockerImageName | String | Si | Nombre de la imagen Docker |
| params.dockerImageTag | String | Si | Tag/version de la imagen Docker |

#### Retorna

`List<String>` - Lista de etiquetas generadas para las imagenes Docker.

#### Ejemplo

```groovy
def tags = dockerBuild.generateTags([
    nexusDockerHost: 'nexus.example.com:8082',
    nexusDockerRepository: 'docker-hosted',
    ecrRegistry: '123456789012.dkr.ecr.us-east-1.amazonaws.com',
    ecrRepository: 'mi-repositorio',
    dockerImageName: 'mi-app',
    dockerImageTag: '1.0.0'
])
// Resultado: [
//   "nexus.example.com:8082/docker-hosted/mi-app:1.0.0",
//   "123456789012.dkr.ecr.us-east-1.amazonaws.com/mi-repositorio/mi-app:1.0.0"
// ]
```

---

### build

Construye una imagen Docker para un servicio especifico utilizando un DockerFileBuild.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros para la construccion |
| params.serviceName | String | Si | Nombre del servicio |
| params.strategy | String | Si | Estrategia de construccion (ej: "docker", "build") |
| params.lang | String | Si | Lenguaje de programacion (ej: "java", "nodejs", "dotnet") |
| params.langVersion | String | Si | Version del lenguaje |
| params.dockerCommand | String | Si | Comando a ejecutar en el contenedor |
| params.imageRegistry | String | Si | Registro de imagenes base |
| params.compileAppFolder | String | Si | Carpeta donde se compila la aplicacion |
| params.appSrc | String | Si | Carpeta de codigo fuente |
| params.containerPort | String | Si | Puerto del contenedor |
| params.runTests | String | Si | Indica si ejecutar tests ("true"/"false") |
| params.artifactID | String | Si | ID del artefacto |
| params.nexusProxyHost | String | Si | Host del proxy de Nexus |
| params.nexusProxyRepository | String | Si | Ruta del repositorio proxy de Nexus |
| params.registryUsername | String | Si | Usuario para autenticacion en el registro |
| params.registryPassword | String | Si | Contraseña para autenticacion en el registro |
| params.npmApiKey | String | No | Token de API para npm |
| params.dependencyCommand | String | No | Comando adicional para gestion de dependencias |
| params.nexusDockerHost | String | No | Host de Docker en Nexus |
| params.nexusDockerRepository | String | No | Repositorio Docker en Nexus |
| params.ecrRegistry | String | No | Registro ECR |
| params.ecrRepository | String | No | Repositorio ECR |
| params.dockerImageName | String | Si | Nombre de la imagen Docker |
| params.dockerImageTag | String | Si | Tag de la imagen Docker |

#### Archivos Copiados

La funcion copia automaticamente los siguientes archivos si existen:
- `../pipeline/${strategy}/${lang}/settings.xml`
- `../pipeline/${strategy}/${lang}/script.sh`
- `../pipeline/${strategy}/${lang}/nginx.conf.template`

#### Dockerfile Utilizado

`../pipeline/${strategy}/${serviceName o lang}/DockerFileBuild`

#### Ejemplo

```groovy
stage('Build') {
    steps {
        dockerBuild.build([
            serviceName: 'mi-api',
            strategy: 'build',
            lang: 'java',
            langVersion: '17',
            dockerCommand: 'java -jar app.jar',
            imageRegistry: 'docker.io',
            compileAppFolder: 'target',
            appSrc: 'src',
            containerPort: '8080',
            runTests: 'true',
            artifactID: 'mi-api',
            nexusProxyHost: 'nexus.example.com',
            nexusProxyRepository: '/repository/maven-public/',
            registryUsername: 'admin',
            registryPassword: 'password',
            nexusDockerHost: 'nexus.example.com:8082',
            nexusDockerRepository: 'docker-hosted',
            dockerImageName: 'mi-api',
            dockerImageTag: '1.0.0'
        ])
    }
}
```

---

### coverage

Ejecuta la cobertura de codigo para un servicio especifico usando Docker y envia los resultados a SonarQube.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros para la cobertura |
| params.serviceName | String | Si | Nombre del servicio |
| params.strategy | String | Si | Estrategia de construccion |
| params.lang | String | Si | Lenguaje de programacion |
| params.langVersion | String | Si | Version del lenguaje |
| params.dockerCommand | String | Si | Comando Docker |
| params.imageRegistry | String | Si | Registro de imagenes base |
| params.compileAppFolder | String | Si | Carpeta de compilacion |
| params.appSrc | String | Si | Carpeta de codigo fuente |
| params.runTests | String | Si | Ejecutar tests ("true"/"false") |
| params.sonarToken | String | Si | Token de autenticacion para SonarQube |
| params.sonarHost | String | Si | URL del servidor SonarQube |
| params.pkgVersion | String | Si | Version del proyecto para SonarQube |
| params.artifactID | String | Si | ID del artefacto |
| params.nexusProxyHost | String | Si | Host del proxy de Nexus |
| params.nexusProxyRepository | String | Si | Repositorio proxy de Nexus |
| params.registryUsername | String | Si | Usuario del registro |
| params.registryPassword | String | Si | Contraseña del registro |
| params.dependencyCommand | String | No | Comando adicional de dependencias |

#### Dockerfile Utilizado

`../pipeline/${strategy}/${serviceName o lang}/DockerFileCoverage`

#### Ejemplo

```groovy
stage('Coverage') {
    steps {
        dockerBuild.coverage([
            serviceName: 'mi-api',
            strategy: 'build',
            lang: 'java',
            langVersion: '17',
            dockerCommand: 'mvn test',
            imageRegistry: 'docker.io',
            compileAppFolder: 'target',
            appSrc: 'src',
            runTests: 'true',
            sonarToken: env.SONAR_TOKEN,
            sonarHost: 'https://sonarqube.example.com',
            pkgVersion: '1.0.0',
            artifactID: 'mi-api',
            nexusProxyHost: 'nexus.example.com',
            nexusProxyRepository: '/repository/maven-public/',
            registryUsername: 'admin',
            registryPassword: 'password'
        ])
    }
}
```

---

### buildWithCoverage

Realiza la construccion y cobertura de codigo para un servicio especifico usando Docker. El Dockerfile debe tener integrado el coverage y build en el mismo archivo, utilizando la variable `SONAR_RUN` para determinar si ejecuta build & coverage o solo build.

#### Proceso de Ejecucion

1. **PASO 1**: Si `runCoverage=true`, ejecuta primero el stage coverage (target: coverage)
2. **PASO 2**: Ejecuta el build normal (target: runner) con todas las tags

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros para construccion y cobertura |
| params.runCoverage | String | Si | Indica si ejecutar coverage ("true"/"false") |
| params.routePath | String | No | Ruta base de la aplicacion |
| (... otros parametros similares a build y coverage ...) | | | |

#### Dockerfile Utilizado

`../pipeline/${strategy}/${serviceName o lang}/DockerFileBuildCoverage`

Debe incluir multi-stage con targets:
- `coverage`: Para analisis de SonarQube
- `runner`: Para imagen final ejecutable

#### Ejemplo

```groovy
stage('Build with Coverage') {
    steps {
        dockerBuild.buildWithCoverage([
            serviceName: 'mi-api',
            strategy: 'build',
            lang: 'nodejs',
            langVersion: '18',
            runCoverage: 'true',
            routePath: '/api',
            dockerCommand: 'npm start',
            imageRegistry: 'docker.io',
            compileAppFolder: 'dist',
            appSrc: 'src',
            containerPort: '3000',
            runTests: 'true',
            sonarToken: env.SONAR_TOKEN,
            sonarHost: 'https://sonarqube.example.com',
            pkgVersion: '1.0.0',
            artifactID: 'mi-api',
            nexusProxyHost: 'nexus.example.com',
            nexusProxyRepository: '/repository/npm-public/',
            registryUsername: 'admin',
            registryPassword: 'password',
            npmApiKey: env.NPM_TOKEN,
            nexusDockerHost: 'nexus.example.com:8082',
            nexusDockerRepository: 'docker-hosted',
            ecrRegistry: '123456789012.dkr.ecr.us-east-1.amazonaws.com',
            ecrRepository: 'mi-repositorio',
            dockerImageName: 'mi-api',
            dockerImageTag: '1.0.0'
        ])
    }
}
```

---

### buildSelector

Orquesta la construccion de la imagen seleccionando automaticamente entre `buildxWithCoverage` (Docker Buildx con cache S3) y `buildWithCoverage` (Docker Build estandar).

Es el **punto de entrada recomendado** para pipelines que quieran aprovechar el cache S3 cuando esta disponible, con fallback automatico al build estandar.

#### Logica de seleccion

```
buildSelector
├── s3CacheCreds + s3CacheBucket configurados?
│   ├── SI → Login AWS → Builder 'devopss3builder' disponible?
│   │         ├── SI → Bucket existe y hay permisos?
│   │         │         ├── exist       → buildxWithCoverage ✓
│   │         │         │     └── Error de infraestructura containerd? → limpia cache → buildWithCoverage
│   │         │         ├── nonexist    → buildWithCoverage (fallback)
│   │         │         └── nopermission → buildWithCoverage (fallback)
│   │         └── NO  → buildWithCoverage (fallback)
│   └── NO → buildWithCoverage (sin cache S3)
```

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros completo (ver `buildxWithCoverage`) |
| params.s3CacheCreds | String | No | ID de credencial AWS en Jenkins para acceder al bucket de cache |
| params.s3CacheBucket | String | No | Nombre del bucket S3 usado para cache de capas Docker |
| params.s3CacheRegion | String | No | Region AWS del bucket (ej: "us-east-1"). Si se omite usa `params.awsRegion` o `us-east-1` |

> Si `s3CacheCreds` o `s3CacheBucket` no estan definidos, se usa `buildWithCoverage` directamente sin intentar buildx.

#### Prerequisitos para usar buildx con cache S3

- El constructor `devopss3builder` debe existir y estar en estado `running` en el agente Jenkins
- La credencial AWS debe tener permisos de lectura/escritura sobre el bucket S3

#### Ejemplo

```groovy
stage('Build & Coverage') {
    steps {
        script {
            dockerBuild.buildSelector([
                serviceName: 'mi-api',
                strategy: 'build',
                lang: 'java',
                langVersion: '17',
                runCoverage: 'true',
                dockerCommand: 'java -jar app.jar',
                imageRegistry: 'docker.io',
                compileAppFolder: 'target',
                appSrc: 'src',
                containerPort: '8080',
                runTests: 'true',
                sonarToken: env.SONAR_TOKEN,
                sonarHost: 'https://sonarqube.example.com',
                pkgVersion: '1.0.0',
                artifactID: 'mi-api',
                nexusProxyHost: 'nexus.example.com',
                nexusProxyRepository: '/repository/maven-public/',
                registryUsername: credentials('registry-user'),
                registryPassword: credentials('registry-pass'),
                dockerImageName: 'mi-api',
                dockerImageTag: "${env.BUILD_NUMBER}",
                // Parametros opcionales para cache S3
                s3CacheCreds: 'aws-cache-credentials',
                s3CacheBucket: 'my-docker-cache-bucket',
                s3CacheRegion: 'us-east-1'
            ])
        }
    }
}
```

---

### buildxWithCoverage

Realiza la construccion y cobertura de codigo usando **Docker Buildx** con cache en bucket S3. Equivalente a `buildWithCoverage` pero con soporte de cache distribuido.

#### Proceso de Ejecucion

1. **PASO 1 (coverage)**: Si `runCoverage=true` y el Dockerfile tiene stage `coverage`, ejecuta `docker buildx build --target coverage` usando solo `--cache-from` (no exporta cache de este stage)
2. **PASO 2 (runner)**: Ejecuta `docker buildx build --load --target runner` usando `--cache-from` y `--cache-to` (importa y exporta cache S3)

#### Estrategia de cache S3

| Stage | cache-from | cache-to |
|-------|-----------|---------|
| coverage | Si | No (stage no reutilizable entre builds) |
| runner | Si | Si (imagen final, genera mayor beneficio) |

Estructura de rutas en S3:
```
s3://<bucket>/cache/<serviceName>
```

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros para construccion y cobertura |
| params.s3CacheCreds | String | Si | ID de credencial AWS en Jenkins |
| params.s3CacheBucket | String | Si | Nombre del bucket S3 para cache |
| params.s3CacheRegion | String | No | Region AWS (default: `us-east-1`) |
| params.s3CacheEndpoint | String | No | Endpoint VPC/S3 personalizado (ej: endpoint privado). Si no se indica, usa `env.DOCKER_CACHE_ENDPOINT` si existe |
| params.s3CacheMode | String | No | Modo de exportacion de cache: `min` (solo capas finales) o `max` (todas las capas). Default: `min` o `env.DOCKER_CACHE_MODE` |
| params.s3CacheExport | String | No | Habilita o deshabilita la exportacion de cache: `true`/`false`. Default: `true` o `env.DOCKER_CACHE_EXPORT` |
| (... parametros comunes de build y coverage ...) | | | Ver seccion `buildWithCoverage` |

#### Prerequisitos

- **Builder**: El constructor `devopss3builder` debe existir en estado `running`
  ```bash
  docker buildx create --name devopss3builder --driver docker-container --use
  docker buildx inspect devopss3builder --bootstrap
  ```
- **Driver**: Debe usar el driver `docker-container` (requerido para cache S3)
- **Credenciales AWS**: La credencial `s3CacheCreds` debe tener permisos `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` sobre el bucket

#### Variables de entorno opcionales

| Variable | Descripcion |
|----------|-------------|
| `DOCKER_CACHE_MODE` | Modo de cache por defecto si no se pasa `s3CacheMode` |
| `DOCKER_CACHE_EXPORT` | Habilitar/deshabilitar export por defecto si no se pasa `s3CacheExport` |
| `DOCKER_CACHE_ENDPOINT` | Endpoint S3 por defecto si no se pasa `s3CacheEndpoint` |

#### Ejemplo

```groovy
stage('Build & Coverage (Buildx)') {
    steps {
        script {
            dockerBuild.buildxWithCoverage([
                serviceName: 'mi-api',
                strategy: 'build',
                lang: 'java',
                langVersion: '17',
                runCoverage: 'true',
                dockerCommand: 'java -jar app.jar',
                imageRegistry: 'docker.io',
                compileAppFolder: 'target',
                appSrc: 'src',
                containerPort: '8080',
                runTests: 'true',
                sonarToken: env.SONAR_TOKEN,
                sonarHost: 'https://sonarqube.example.com',
                pkgVersion: '1.0.0',
                artifactID: 'mi-api',
                nexusProxyHost: 'nexus.example.com',
                nexusProxyRepository: '/repository/maven-public/',
                registryUsername: credentials('registry-user'),
                registryPassword: credentials('registry-pass'),
                dockerImageName: 'mi-api',
                dockerImageTag: "${env.BUILD_NUMBER}",
                s3CacheCreds: 'aws-cache-credentials',
                s3CacheBucket: 'my-docker-cache-bucket',
                s3CacheRegion: 'us-east-1',
                s3CacheMode: 'min',
                s3CacheExport: 'true'
            ])
        }
    }
}
```

---

### buildLocal

Construye una imagen Docker localmente con parametros basicos.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros |
| params.dockerName | String | Si | Nombre de la imagen |
| params.version | String | Si | Version de la aplicacion |
| params.nexusUser | String | Si | Usuario de Nexus |
| params.nexusPassword | String | Si | Contraseña de Nexus |
| params.dockerTags | String | Si | Etiquetas separadas por espacios |
| params.dockerPath | String | Si | Ruta al contexto de construccion |

#### Configuracion

Utiliza `--network=host` para permitir acceso a servicios locales durante la construccion.

#### Ejemplo

```groovy
dockerBuild.buildLocal([
    dockerName: 'mi-app',
    version: '1.0.0',
    nexusUser: 'admin',
    nexusPassword: 'password',
    dockerTags: 'mi-app:latest mi-app:1.0.0',
    dockerPath: './docker'
])
```

---

### buildDocker

Construye una imagen Docker para un servicio especifico utilizando la estrategia Docker.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| params | Map | Si | Mapa de parametros |
| params.serviceName | String | Si | Nombre del servicio |
| params.imageRegistry | String | Si | Registro de imagenes |
| params.langVersion | String | Si | Version del lenguaje |
| params.version | String | Si | Version del servicio |
| params.dockerTags | String | Si | Etiquetas Docker |
| params.strategy | String | Si | Estrategia de construccion |

#### Dockerfile Utilizado

`../pipeline/${strategy}/${serviceName}/DockerFile`

#### Ejemplo

```groovy
dockerBuild.buildDocker([
    serviceName: 'mi-app',
    imageRegistry: 'docker.io',
    langVersion: '17',
    version: '1.0.0',
    dockerTags: '-t mi-app:latest -t mi-app:1.0.0',
    strategy: 'docker'
])
```

---

### dockerLogin

Realiza un login a una registry Docker.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| dockerUserId | String | Si | ID de credencial configurada en Jenkins |
| dockerRegistry | String | Si | URL de la registry Docker |

#### Validaciones

- Valida que la URL de la registry este disponible antes de intentar el login
- Maneja errores comunes de credenciales y conectividad

#### Ejemplo

```groovy
stage('Login to Registry') {
    steps {
        dockerBuild.dockerLogin(
            'nexus-docker-credentials',
            'nexus.example.com:8082'
        )
    }
}
```

---

### handleErrorRegistry

Maneja las excepciones comunes de Jenkins y Docker, proporcionando mensajes de error especificos.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| exception | Exception | Si | La excepcion capturada |
| registry | String | Si | Nombre de la registry Docker |
| userId | String | No | ID del usuario Docker |

#### Errores Manejados

- Credenciales no encontradas
- Respuestas HTTP a cliente HTTPS
- Fallo en comando Docker login
- Host no resuelto
- Errores generales

#### Ejemplo

```groovy
try {
    dockerBuild.dockerLogin('my-creds', 'registry.example.com')
} catch (Exception e) {
    dockerBuild.handleErrorRegistry(e, 'registry.example.com', 'my-creds')
}
```

---

### dockerBuildWithArgsFile

Construye una imagen Docker utilizando los argumentos definidos en el archivo `docker_build.args`.

#### Descripcion

- Autentica con credenciales de Nexus y SonarQube definidas en Jenkins
- Usa `docker build` con multiples etiquetas
- Lee argumentos de construccion desde el archivo `docker_build.args`

#### Tags Generadas

- `${DOCKER_IMAGE_NAME}:latest`
- `${NEXUS_DOCKER_HOST}/${NEXUS_DOCKER_REPOSITORY}/${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}`
- `${ECR_REGISTRY}/${ECR_REPOSITORY}/${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_TAG}`
- `${ECR_REGISTRY}/${ECR_REPOSITORY}/${DOCKER_IMAGE_NAME}:latest`

#### Variables de Entorno Requeridas

- `NEXUS_CREDENTIAL_ID`
- `SONAR_LOGIN`
- `DOCKER_IMAGE_NAME`
- `DOCKER_IMAGE_TAG`
- `NEXUS_DOCKER_HOST`
- `NEXUS_DOCKER_REPOSITORY`
- `ECR_REGISTRY`
- `ECR_REPOSITORY`

#### Archivos Requeridos

- `docker_build.args`: Archivo con argumentos de construccion
- `docker/Dockerfile`: Dockerfile a utilizar

#### Ejemplo

```groovy
stage('Build with Args File') {
    steps {
        script {
            env.NEXUS_CREDENTIAL_ID = 'nexus-creds'
            env.SONAR_LOGIN = 'sonar-creds'
            env.DOCKER_IMAGE_NAME = 'mi-app'
            env.DOCKER_IMAGE_TAG = '1.0.0'
            env.NEXUS_DOCKER_HOST = 'nexus.example.com:8082'
            env.NEXUS_DOCKER_REPOSITORY = 'docker-hosted'
            env.ECR_REGISTRY = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
            env.ECR_REPOSITORY = 'mi-repositorio'

            dockerBuild.dockerBuildWithArgsFile()
        }
    }
}
```

---

### getFirstFromImage

Extrae el nombre de la imagen de la primera instruccion FROM valida en un Dockerfile.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| dockerfileContent | String | Si | El contenido completo del Dockerfile |
| dockerVersion | String | No | Valor para reemplazar el placeholder `${VERSION}` |

#### Retorna

`String` - El nombre de la imagen base o `null` si no se encuentra.

#### Caracteristicas

- Ignora lineas de comentario
- Elimina alias (ej: "AS builder")
- Reemplaza placeholders `${VERSION}` si se proporciona dockerVersion

#### Ejemplo

```groovy
def dockerfileContent = readFile('Dockerfile')
def baseImage = dockerBuild.getFirstFromImage(dockerfileContent, '8.0')
// Si el Dockerfile contiene: FROM mcr.microsoft.com/dotnet/aspnet:${VERSION} AS base
// Retorna: "mcr.microsoft.com/dotnet/aspnet:8.0"
```

---

### resolveDockerfilePath

Resuelve la ruta completa a un Dockerfile dentro de un directorio dado, buscando tanto 'Dockerfile' como 'dockerfile'.

#### Parametros

| Nombre | Tipo | Requerido | Descripcion |
|--------|------|-----------|-------------|
| dockerPath | String | Si | El directorio donde buscar el Dockerfile |

#### Retorna

`String` - La ruta completa al Dockerfile encontrado.

#### Excepciones

Lanza una excepcion si no se encuentra 'Dockerfile' ni 'dockerfile' en la ruta especificada.

#### Ejemplo

```groovy
def dockerfilePath = dockerBuild.resolveDockerfilePath('./docker')
// Retorna: "./docker/Dockerfile" o "./docker/dockerfile"
```

---

## Notas Importantes

### Seguridad

- Las contraseñas se ocultan en los logs usando `set +x`
- Se recomienda usar credenciales de Jenkins en lugar de valores hardcodeados
- Los tokens y passwords deben gestionarse con `withCredentials`

### Optimizacion

- Se usa `--cpu-shares 2048` para limitar el uso de CPU durante la construccion
- Se usa `--no-cache` para garantizar construcciones limpias en builds estandar
- Se usa `--network=host` en construcciones locales
- `buildxWithCoverage` reduce el tiempo de build aproximadamente un **35%** reutilizando capas cacheadas en S3
- El cache S3 esta segregado por `serviceName` para evitar colisiones entre servicios
- Solo se exporta cache del stage `runner` (imagen final); el stage `coverage` solo importa para no contaminar el cache compartido

### Docker Buildx y cache S3

- El cache S3 requiere el driver `docker-container` (no compatible con el driver `docker` por defecto)
- Si el builder `devopss3builder` no esta disponible o el bucket no es accesible, `buildSelector` hace fallback automatico a `buildWithCoverage` sin interrumpir el pipeline
- Si buildx falla por errores transitorios de `containerd` (mounts colgados, `EBUSY`), `buildSelector` limpia el cache buildx automaticamente y reintenta con build estandar
- El modo de cache `min` exporta solo las capas de la imagen final (recomendado). El modo `max` exporta todas las capas intermedias (mayor hit rate, mayor uso de almacenamiento S3)

### Manejo de Errores

- Todas las funciones de construccion capturan excepciones y las reportan
- Los mensajes de error se almacenan en `env.MENSAJE`
- Se proporcionan detalles especificos del error en los logs

### Multi-Registry

- Las funciones soportan push simultaneo a Nexus y ECR
- Las tags se generan automaticamente para ambos registros
- Se puede configurar uno o ambos registros segun necesidad

---

## Dependencias

- `validateFunctions`: Biblioteca para validacion de URLs
- `awsS3Functions`: Biblioteca para login AWS y verificacion de buckets S3 (requerida por `buildSelector` y `buildxWithCoverage`)
- `cleanUpFunctions`: Biblioteca para limpieza de cache buildx en caso de errores de infraestructura (requerida por `buildSelector`)
- Docker instalado en el agente de Jenkins
- Variables de entorno de Jenkins
- Credenciales configuradas en Jenkins

### Constructor Docker Buildx (para buildSelector / buildxWithCoverage)

El constructor `devopss3builder` se despliega mediante un rol de Ansible en el repositorio [alm-svc-ansible](https://bitbucket.org/example/alm-svc-ansible/src/main/roles/docker-buildx/).

El rol debe ejecutarse sobre el agente Jenkins antes de usar pipelines con cache S3. Una vez desplegado, el constructor queda persistente en el agente.

> Sin este constructor activo, `buildSelector` hace fallback automatico a `buildWithCoverage` (build estandar sin cache).

---

## Ejemplo Completo de Pipeline

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        NEXUS_CREDENTIAL_ID = 'nexus-credentials'
        SONAR_LOGIN = 'sonar-credentials'
    }

    stages {
        stage('Login to Nexus') {
            steps {
                script {
                    dockerBuild.dockerLogin(
                        env.NEXUS_CREDENTIAL_ID,
                        'nexus.example.com:8082'
                    )
                }
            }
        }

        stage('Build & Coverage') {
            steps {
                script {
                    // buildSelector selecciona automaticamente entre buildx (con cache S3) y build estandar
                    dockerBuild.buildSelector([
                        serviceName: 'mi-api',
                        strategy: 'build',
                        lang: 'java',
                        langVersion: '17',
                        runCoverage: 'true',
                        dockerCommand: 'java -jar app.jar',
                        imageRegistry: 'docker.io',
                        compileAppFolder: 'target',
                        appSrc: 'src',
                        containerPort: '8080',
                        runTests: 'true',
                        sonarToken: credentials('sonar-token'),
                        sonarHost: 'https://sonarqube.example.com',
                        pkgVersion: '1.0.0',
                        artifactID: 'mi-api',
                        nexusProxyHost: 'nexus.example.com',
                        nexusProxyRepository: '/repository/maven-public/',
                        registryUsername: credentials('registry-user'),
                        registryPassword: credentials('registry-pass'),
                        nexusDockerHost: 'nexus.example.com:8082',
                        nexusDockerRepository: 'docker-hosted',
                        dockerImageName: 'mi-api',
                        dockerImageTag: "${env.BUILD_NUMBER}",
                        // Cache S3 (opcional - si se omite usa build estandar)
                        s3CacheCreds: 'aws-cache-credentials',
                        s3CacheBucket: 'my-docker-cache-bucket',
                        s3CacheRegion: 'us-east-1'
                    ])
                }
            }
        }
    }

    post {
        failure {
            echo "Build failed: ${env.MENSAJE}"
        }
    }
}
```
..

**Tags:** `#docker`, `#dockerbuild`, `#dockercoverage`, `#jenkins`, `#pipeline`, `#nexus`, `#ecr`, `#sonarqube`