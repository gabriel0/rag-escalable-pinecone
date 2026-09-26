# Funciones de Flujo de Despliegue (apimFlowDeploy)

Esta libreria orquesta el ciclo de vida completo del despliegue de una aplicacion, desde la compilacion y construccion de imagenes hasta el despliegue en diferentes entornos y la promocion a produccion.

## `toEnvironment`

Funcion principal que despliega una aplicacion en un entorno especifico. El comportamiento de la funcion varia significativamente dependiendo del entorno de destino (`develop`, `testing`, `pre`, `prod`).

Existen funciones de ayuda que simplifican la llamada a esta funcion:
- `toDevelop(appRepoName)`
- `toTesting(appRepoName)`
- `toPre(appRepoName)`
- `toProd(appRepoName)`

### Parametros

- `appRepoName` (String, **Obligatorio**): La URL del repositorio Git de la aplicacion.
- `envName` (String, **Obligatorio**): El nombre del entorno de destino. Valores validos: `develop`, `testing`, `pre`, `prod`.

### Logica de Ejecucion

#### Para entornos `develop` y `testing`:

1.  **Clonado de Codigo**: Clona el repositorio desde la rama especificada en la variable de entorno `BRANCH`.
2.  **Construccion de Imagen (Opcional)**:
    - Si la variable `IMAGE_BUILD` es `true`:
        - **Creacion de Version (Solo en `testing`)**: Si no existen tags de `release` o `hotfix`, crea una nueva version y su tag correspondiente.
        - **Construccion**: Compila el codigo y construye una nueva imagen Docker.
        - **Escaneo de Seguridad (Opcional)**: Si `TRIVY_SCAN` es `true`, escanea la imagen con Trivy.
        - **Subida a Registros**: Sube la imagen al registro Nexus de desarrollo y al registro de artefactos de GCP.
3.  **Seleccion de Imagen (Opcional)**:
    - Si `IMAGE_BUILD` es `false` y `DEPLOY_MICROSERVICE` es `true`:
        - Muestra un menu interactivo para seleccionar una version de imagen existente desde el registro Nexus de desarrollo.
4.  **Despliegue en Kubernetes**:
    - Se autentica en GCP y configura el acceso al cluster de GKE.
    - Despliega la aplicacion utilizando `helm install`.

#### Para entornos `pre` y `prod`:

1.  **Seleccion de Imagen**: Muestra un menu interactivo para seleccionar una version de imagen desde el registro Nexus de **produccion**.
2.  **Transferencia de Imagen**: Descarga la imagen seleccionada de Nexus, la re-etiqueta para GCP y la sube al registro de artefactos de GCP del entorno correspondiente.
3.  **Validacion de Pre-Produccion (Solo en `prod`)**: Antes de desplegar en `prod`, verifica que la version seleccionada ya se encuentre desplegada y activa en el entorno `pre`.
4.  **Despliegue en Kubernetes**: Si las validaciones son correctas, se autentica en GCP, configura el acceso al cluster y despliega la aplicacion con `helm install`.

### Variables de Entorno Requeridas (Ejemplos)

- `BRANCH`: Rama a utilizar para `develop` y `testing`.
- `CREDENTIAL_GIT`: ID de la credencial de Jenkins para Git.
- `CREDENTIAL_NEXUS`: ID de la credencial para el Nexus de desarrollo.
- `CREDENTIAL_NEXUS_PROD`: ID de la credencial para el Nexus de produccion.
- `IMAGE_BUILD`: `true` o `false`. Indica si se debe construir una nueva imagen.
- `DEPLOY_MICROSERVICE`: `true` o `false`. Indica si se debe desplegar el microservicio.
- `DEPLOY_TYPE`: `release` o `hotfix`. Usado al crear una nueva version.
- `GCP_ARTIFACT_CREDENTIAL_ID`: ID de la credencial de GCP.
- `GCP_PROJECT`, `GCP_GKE_CLUSTER`, `GCP_REGION`: Configuracion del cluster de destino.
- `POM_PATH`: Ruta al `pom.xml` si es un proyecto Maven.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Deploy to Testing') {
    steps {
        script {
            // Se asume que las variables de entorno estan cargadas
            apimFlowDeploy.toTesting('git@bitbucket.org:mi-org/mi-repo.git')
        }
    }
}
```

---

## `acceptToEnvironment`

Formaliza la promocion de una version a un entorno productivo (tipicamente `prod`) mediante la fusion de su tag de `release` o `hotfix` en la rama principal (`master`). Esta accion representa la "aceptacion" final del cambio.

Existe una funcion de ayuda que simplifica la llamada:
- `acceptToProd(appRepoName)`

### Parametros

- `appRepoName` (String, **Obligatorio**): La URL del repositorio Git de la aplicacion.
- `envName` (String, **Obligatorio**): El nombre del entorno desde el cual se acepta el despliegue (ej. `prod`).

### Logica de Ejecucion

1.  **Seleccion de Tag**: Muestra un menu interactivo para que el usuario seleccione un tag de tipo `release-*` o `hotfix-*` que se desea promocionar.
2.  **Validacion de Despliegue**: Confirma que la version correspondiente al tag seleccionado este actualmente desplegada y activa en el cluster de Kubernetes del entorno especificado.
3.  **Validacion de Fusion**: Verifica que el commit del tag no haya sido ya fusionado en la rama `master` para evitar dobles fusiones.
4.  **Fusion y Etiquetado**:
    - Si todas las validaciones son exitosas:
        - Fusiona (`merge`) el tag seleccionado en la rama `master`.
        - Elimina el tag original (`release-*` o `hotfix-*`).
        - Actualiza el tag `prod-stable` para que apunte al nuevo `HEAD` de `master`.
        - Crea un nuevo tag `prod-<version>` para marcar la version de produccion.
        - Elimina la rama de feature asociada (`develop` o `hotfix`).
5.  **Aborto**: Si alguna de las validaciones falla, el pipeline se detiene con un error.

### Variables de Entorno Requeridas (Ejemplos)

- `CREDENTIAL_GIT`: ID de la credencial de Jenkins para Git.
- `GCP_ARTIFACT_CREDENTIAL_ID`: ID de la credencial de GCP.
- `GCP_PROJECT`, `GCP_GKE_CLUSTER`, `GCP_REGION`: Configuracion del cluster de destino.
- `NAMESPACE`: Namespace de Kubernetes donde se verifica el despliegue.

### Ejemplo de Uso en Jenkinsfile

```groovy
stage('Accept to Production') {
    steps {
        script {
            // Se invoca despues de un despliegue exitoso en 'prod'
            // para formalizar el cambio en el control de versiones.
            apimFlowDeploy.acceptToProd('git@bitbucket.org:mi-org/mi-repo.git')
        }
    }
}
```