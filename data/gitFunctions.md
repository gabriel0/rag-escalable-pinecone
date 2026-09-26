# Funciones de Git

Esta libreria proporciona un conjunto de funciones de utilidad para interactuar con repositorios Git desde un pipeline de Jenkins. Estas funciones simplifican operaciones comunes como verificar la existencia de ramas y tags, crear nuevos tags y comparar historiales de commits, lo cual es fundamental para implementar flujos de trabajo como GitFlow.

## Metodos

### `getTagsCountOnReversePosition(filter, count)`

Obtiene un numero especifico de tags de Git, ordenados de forma descendente (por version), con la opcion de filtrarlos usando una expresion regular.

-   **Parametros:**
    -   `filter` (String): Una expresion regular para filtrar los tags.
    -   `count` (Integer): El numero maximo de tags a devolver.
-   **Respuesta:**
    -   (String) Una lista de tags que coinciden con el filtro, separados por saltos de linea.

---

### `getReleaseBranches(filter, count)`

Obtiene las ramas de release, de manera similar a `getTagsCountOnReversePosition`.

-   **Parametros:**
    -   `filter` (String): Una expresion regular para filtrar los nombres de las ramas.
    -   `count` (Integer): El numero maximo de ramas a devolver.
-   **Respuesta:**
    -   (String) Una lista de ramas que coinciden con el filtro.

---

### `lastCommitIsInHistory(ref1, ref2)`

Verifica si el ultimo commit de una referencia (`ref1`) esta presente en el historial de otra referencia (`ref2`). Es util para asegurar que un tag corresponde al ultimo commit de una rama.

-   **Parametros:**
    -   `ref1` (String): La referencia (rama o tag) cuyo ultimo commit se verificara.
    -   `ref2` (String): La referencia donde se buscara el historial de commits.
-   **Respuesta:**
    -   `true` si el commit esta en el historial; `false` en caso contrario.

---

### `branchExist(branchName)`

Comprueba si una rama con el nombre especificado existe en el repositorio remoto.

-   **Parametros:**
    -   `branchName` (String): El nombre de la rama a verificar.
-   **Respuesta:**
    -   `true` si la rama existe; `false` en caso contrario.

---

### `tagAlreadyExist(tagName)`

Comprueba si un tag con el nombre especificado ya existe en el repositorio.

-   **Parametros:**
    -   `tagName` (String): El nombre del tag a verificar.
-   **Respuesta:**
    -   `true` si el tag existe; `false` en caso contrario.

---

### `tagCreateFromBranch(tagName, branchName)`

Crea un nuevo tag apuntando a la cabecera (HEAD) de una rama especifica y lo sube al repositorio remoto.

-   **Parametros:**
    -   `tagName` (String): El nombre del tag a crear.
    -   `branchName` (String): El nombre de la rama que se va a etiquetar.

## Ejemplo de Uso

```groovy
// En un Jenkinsfile o libreria compartida

stage('Validar Cumplimiento de GitFlow') {
    steps {
        script {
            def releaseBranch = "release/1.2.0"
            def releaseTag = "v1.2.0"

            if (gitFunctions.branchExist(releaseBranch) && !gitFunctions.tagAlreadyExist(releaseTag)) {
                echo "Creando el tag ${releaseTag} desde la rama ${releaseBranch}."
                gitFunctions.tagCreateFromBranch(releaseTag, releaseBranch)
            } else {
                echo "El tag ya existe o la rama de release no fue encontrada."
            }
        }
    }
}
```

## Estrategia de librerias

`checkoutLibrarySourceFromEvent` implementa la estrategia de publicacion de librerias:

- Commits en `develop`: checkout de branch `develop` y publicacion `snapshot`.
- Tags `release-*`: checkout del tag y publicacion `release`.
- El tag `release-x.y.z` debe existir sobre una rama de release:
  - si existe la rama `releases` (a secas), se usa esa como origen;
  - si no existe, se exige la rama versionada `release/x.y.z`.
- Cualquier otra branch o tag aborta con error controlado.

Variables seteadas:

- `env.LIB_SOURCE_REF`: branch o tag usado como fuente.
- `env.LIB_PUBLICATION_TYPE`: `snapshot` o `release`.
- `env.TAG_NAME`: solo se setea para releases; en snapshots queda vacio.
- `env.LIB_RELEASE_BRANCH`: rama `releases` o `release/x.y.z`, solo para releases.

## Flujo recomendado de release

1. Trabajar en `develop` con version snapshot, por ejemplo `1.2.0-SNAPSHOT`.
2. Crear rama `release/1.2.0` desde `develop`, o usar la rama fija `releases`.
3. Cambiar la version del paquete en esa rama a `1.2.0`.
4. Crear el tag `release-1.2.0` sobre la rama de release correspondiente.
5. Volver a `develop` y avanzar a la siguiente snapshot, por ejemplo `1.3.0-SNAPSHOT`.

## Uso

```groovy
gitFunctions.checkoutLibrarySourceFromEvent([
    repoUrl          : env.GIT_REPO,
    credentialsId    : env.CREDENTIAL_GIT,
    targetDir        : 'application',
    branch           : params.BRANCH,
    gitlabActionType : env.gitlabActionType,
    gitlabSourceBranch: env.gitlabSourceBranch,
    gitlabBranch     : env.gitlabBranch
])
```

## Compatibilidad

`checkoutTagFromEvent` delega en `checkoutLibrarySourceFromEvent`.

**Tags:** `#git`, `#commit`, `#code`