# Ramas de feature APIM (apimFlowFeature)

Crea, borra y fusiona ramas (o tags) de un repositorio de aplicacion. Siempre clona en el directorio temporal `tempDirForCloning` usando la credencial SSH `jenkins-ssh-key` y `gitFunctions`.

## `create`

Crea una rama nueva desde el ultimo tag `prod-*`, sin validar otras ramas.

### Parametros

- `newBranchName` (String, **Obligatorio**): nombre de la rama a crear.
- `repoName` (String, **Obligatorio**): URL del repositorio Git.

### Respuesta

No retorna valor. Delega en `createWithExtraValidation` con lista de exclusion vacia. Esa lista igual recibe `newBranchName`, asi que la rama no se crea si ya existe.

### Ejemplo

```groovy
apimFlowFeature.create('feature/APIM-123', 'git@bitbucket.org:org/mi-app.git')
```

---

## `createWithExtraValidation`

Igual que `create`, y ademas aborta si alguna rama de la lista ya existe.

### Parametros

- `newBranchName` (String, **Obligatorio**).
- `repoName` (String, **Obligatorio**).
- `listOfExcludedBranchs` (List, **Obligatorio**): nombres que no deben existir. El metodo agrega `newBranchName` a la misma lista.

### Logica

1. `gitFunctions.repoFetchAndShift`.
2. Si ninguna rama de la lista existe, `gitFunctions.branchCreateFromTag` desde `gitFunctions.getLatestTagFromExpression("prod-*")`.
3. Si alguna existe, marca el build `ABORTED` y falla: `Branch {nombre} couldnt be created because any of {lista} already exist`.

### Respuesta

No retorna valor.

---

## `delete`

Borra una rama remota del repositorio.

### Parametros

- `branchName` (String, **Obligatorio**).
- `repoName` (String, **Obligatorio**).

### Respuesta

No retorna valor. Llama a `gitFunctions.branchDelete`.

---

## `merge`

Fusiona un tag o una rama sobre una rama destino.

### Parametros

- `sourceName` (String, **Obligatorio**): nombre de tag o de rama origen.
- `targetBranchName` (String, **Obligatorio**): rama destino.
- `repoName` (String, **Obligatorio**).

### Logica

Si `gitFunctions.getLatestTagFromExpression(sourceName)` devuelve un string con longitud mayor a 0, trata `sourceName` como tag (`gitFunctions.tagMerge`). Si no, lo trata como rama (`gitFunctions.branchMerge`).

### Respuesta

No retorna valor.

**Tags:** `#apim`, `#git`
