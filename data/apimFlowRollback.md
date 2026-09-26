# Rollback de despliegue APIM (apimFlowRollback)

Vuelve a desplegar en Kubernetes el tag `release-*` o `hotfix-*` anterior al ultimo, y puede borrar el tag que quedo en transito.

Depende de `deployFunctions`, `gitFunctions`, `gcpFunctions`, `k8sFunctions` y `artifactRegistryFunctions`.

## `lastDeployOnTesting`

Atajo de rollback en `testing`.

### Parametros

- `appRepoName` (String, **Obligatorio**): URL del repositorio Git.

### Respuesta

El tag que se vuelve a desplegar (mismo valor que `lastDeployOnEnvironment`).

```groovy
def tag = apimFlowRollback.lastDeployOnTesting('git@bitbucket.org:org/mi-app.git')
```

---

## `lastDeployOnPre`

Atajo de rollback en `pre`.

### Parametros

- `appRepoName` (String, **Obligatorio**).

### Respuesta

Tag redesplegado.

---

## `lastDeployOnEnvironment`

Redespliega la version inmediatamente anterior a la ultima `release-*` o `hotfix-*`.

### Parametros

- `appRepoName` (String, **Obligatorio**). El nombre de app es el ultimo segmento de la URL, sin extension.
- `envName` (String, **Obligatorio**): entorno que carga `deployFunctions.loadEnv` (`testing` o `pre` en los atajos).

### Logica

1. Carga variables del entorno.
2. Con `CREDENTIAL_GIT` (SSH), hace fetch en `{appName}_{envName}`.
3. Toma el tag en posicion inversa `1` que matchee `release.*|hotfix.*` (`gitFunctions.getTagOnReversePosition`). La posicion `0` es el ultimo tag; `1` es el anterior.
4. Separa tipo y version por el primer `-`.
5. `env.VERSION` = `deployFunctions.getDowngradedAppVersion(version, tipo)`.
6. Si `VERSION` queda igual a la version del tag elegido, marca el build `ABORTED` y falla con `Verify function, not working as expected.`
7. `deployFunctions.buildVarsForDeploy`.
8. Login GCP (`GCP_ARTIFACT_CREDENTIAL_ID`), `setGkeAuth` y `k8sFunctions.helmInstall` con microservicio activo y config compartida de namespace en `false`.

### Variables de entorno

Las define `deployFunctions.loadEnv`. Este flujo usa en forma directa:

- `CREDENTIAL_GIT`
- `GCP_ARTIFACT_CREDENTIAL_ID`, `GCP_PROJECT`, `GCP_GKE_CLUSTER`, `GCP_REGION`

### Respuesta

String `previousDeployedTag` (tag que se redespliega).

---

## `rollbackIssueInTransit`

Hace rollback en `testing` y despues intenta borrar ese tag en Git.

### Parametros

- `appRepoName` (String, **Obligatorio**).

### Logica

1. `deployFunctions.loadEnv(appName, "testing")`.
2. Asegura la imagen local `gcp_helm_kube:1.0.0` a partir de `registry.example.com:8082/docker-agents/gcp_helm_kube:1.0.0` (`CREDENTIAL_NEXUS`).
3. Llama a `lastDeployOnTesting` y guarda el tag devuelto.
4. Si `gitFunctions.tagAlreadyExist` es falso, fetch del repo y `gitFunctions.branchDelete("tags/"+tag)`.
5. Si el tag ya no existe, no borra nada.

### Respuesta

No retorna valor.

### Ejemplo

```groovy
apimFlowRollback.rollbackIssueInTransit('git@bitbucket.org:org/mi-app.git')
```

**Tags:** `#apim`, `#rollback`, `#helm`
