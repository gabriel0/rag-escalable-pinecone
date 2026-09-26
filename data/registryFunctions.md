# Funciones de Registro de Contenedores (Registry)

Esta libreria proporciona funciones para interactuar con registros de contenedores como AWS ECR y Sonatype Nexus. La funcionalidad principal es validar si una version especifica de una imagen Docker ya existe en un repositorio, lo cual es util en pipelines de CI/CD para evitar sobreescribir artefactos inmutables.

## Metodos

### `validateImageVersion(repositoryType, repositoryName, imageName, imageTag, registryCredId)`

Funcion principal que orquesta la validacion de una version de imagen en un registro. Actua como un despachador que invoca la funcion especifica para el tipo de registro (ECR o Nexus).

-   **Parametros:**
    -   `repositoryType` (String): El tipo de registro. Valores soportados: `'ECR'`, `'NEXUS'`.
    -   `repositoryName` (String): El nombre del repositorio en el registro. Para ECR, puede incluir un prefijo (ej. `mi-app/mi-servicio`).
    -   `imageName` (String): El nombre de la imagen a validar.
    -   `imageTag` (String): La etiqueta (version) de la imagen a buscar.
    -   `registryCredId` (String): El ID de las credenciales de Jenkins para autenticarse con el registro.
-   **Comportamiento:**
    -   Si `imageTag` es `"latest"`, la funcion retorna `false` inmediatamente, ya que la etiqueta `latest` se considera mutable.
    -   Invoca la funcion de validacion correspondiente (`validateEcrImageVersion` o `validateNexusImageVersion`) segun el `repositoryType`.
    -   Captura excepciones comunes (como repositorio no encontrado) para evitar fallos en el pipeline.
-   **Respuesta:**
    -   `true` si la imagen con la etiqueta especificada ya existe.
    -   `false` si la imagen no existe.
    -   Establece la variable de entorno `env.MENSAJE_REGISTRY` con un mensaje informativo si la imagen ya existe.

---

### Funciones Internas (Privadas)

Las siguientes funciones son utilizadas internamente por `validateImageVersion` y no estan pensadas para ser llamadas directamente desde un pipeline.

-   **`validateEcrImageVersion(...)`**: Se conecta a AWS ECR y utiliza el comando `aws ecr describe-images` para verificar la existencia de la etiqueta de la imagen.
-   **`validateNexusImageVersion(...)`**: Se conecta a un registro Nexus a traves de su API REST para buscar la imagen y la version especificadas. Maneja la paginacion de la API.
-   **`registryHandleException(...)`**: Maneja excepciones especificas de los registros (ej. `RepositoryNotFoundException`, `AccessDeniedException`) para que no detengan el pipeline, imprimiendo en su lugar un mensaje informativo.

## Ejemplo de Uso

Esta funcion se utiliza tipicamente en un pipeline de Jenkins antes de la etapa de construccion de la imagen para decidir si es necesario construirla o si ya existe.

```groovy
// En un Jenkinsfile o libreria compartida

def imageExists = false

stage('Validar Imagen Existente') {
    steps {
        script {
            // Validar en AWS ECR
            imageExists = validateFunctions.validateImageVersion(
                repositoryType: 'ECR',
                repositoryName: "${env.ECR_REPOSITORY}",
                imageName: env.IMAGE_NAME,
                imageTag: env.APP_VERSION,
                registryCredId: env.AWS_CREDENTIALS_ID
            )
            // Validar en NEXUS
            imageExists = validateFunctions.validateImageVersion(
                repositoryType: 'NEXUS',
                repositoryName: env.NEXUS_REPOSITORY,
                imageName: env.IMAGE_NAME,
                imageTag: env.APP_VERSION,
                registryCredId: env.NEXUS_CREDENTIALS_ID
            )
        }
    }
}
```

**Tags:** `#registry`, `#docker`, `#ecr`, `#nexus`, `#validate`