# Promocion de imagen APIM (apimFlowPromote)

Copia una imagen Docker desde el Nexus de origen al Nexus de produccion. No despliega en Kubernetes: el despliegue queda en `apimFlowDeploy`.

## `toPre`

Atajo de promocion al entorno `pre`.

### Parametros

- `appRepoName` (String, **Obligatorio**): URL del repositorio Git. El nombre de app es el ultimo segmento de la URL, sin extension.

### Respuesta

No retorna valor. Llama a `toEnvironment(appRepoName, "pre")`.

### Ejemplo

```groovy
apimFlowPromote.toPre('git@bitbucket.org:org/mi-app.git')
```

---

## `toEnvironment`

Selecciona una version publicada y la mueve de registro.

### Parametros

- `appRepoName` (String, **Obligatorio**).
- `envName` (String, **Obligatorio**): entorno cuyas variables carga `deployFunctions.loadEnv`. `toPre` pasa `pre`.

### Logica

1. Carga el entorno de la app.
2. Menu de versiones con `menuAndSelectionFunctions.selectVersionMultiuse("docker", ...)` sobre el Nexus de produccion (`CREDENTIAL_NEXUS_PROD`, `NEXUS_URL_PROD`, `APIM_NEXUS_DOCKER_DIR`, `MICROSERVICE_NAME`, `COUNT_VERSION=5`).
3. Arma las referencias con `buildVarsForPromotion`.
4. Login `onPrem` con `CREDENTIAL_NEXUS`, pull de `DOCKER_SOURCE_IMAGE_AND_TAG`.
5. Retag hacia `DOCKER_DESTINATION_IMAGE_AND_TAG` y borra la imagen origen local.
6. Login con tipo `onPremProd` y `CREDENTIAL_NEXUS_PROD`, push de la imagen destino y borrado local.

`artifactRegistryFunctions.registryLogin` implementa `onPrem`, `gcp` y `ecr`. El tipo `onPremProd` no tiene rama en ese switch: el closure de push no se ejecuta.

### Variables de entorno

Las carga `deployFunctions.loadEnv`. Esta libreria usa:

- `CREDENTIAL_NEXUS`, `CREDENTIAL_NEXUS_PROD`
- `NEXUS_URL_PROD`
- `APIM_NEXUS_DOCKER_DIR`, `APIM_NEXUS_DOCKER_URL`, `APIM_NEXUS_PROD_DOCKER_URL`
- `MICROSERVICE_NAME`
- `VERSION` (la setea el menu de seleccion, antes de `buildVarsForPromotion`)

### Respuesta

No retorna valor.

---

## `buildVarsForPromotion`

Calcula nombres de imagen origen y destino a partir del entorno ya cargado.

### Parametros

Ninguno.

### Variables que escribe

- `DOCKER_IMAGE_TAG` = `VERSION`
- `DOCKER_IMAGE_SINGLE_NAME` = `MICROSERVICE_NAME` en minusculas
- `DOCKER_SOURCE_IMAGE_NAME` = `{APIM_NEXUS_DOCKER_URL}/{APIM_NEXUS_DOCKER_DIR}/{nombre}`
- `DOCKER_DESTINATION_IMAGE_NAME` = `{APIM_NEXUS_PROD_DOCKER_URL}/{APIM_NEXUS_DOCKER_DIR}/{nombre}`
- `DOCKER_SOURCE_IMAGE_AND_TAG` y `DOCKER_DESTINATION_IMAGE_AND_TAG` (nombre + `:{DOCKER_IMAGE_TAG}`)

### Respuesta

No retorna valor. Imprime las cuatro variables principales.

**Tags:** `#apim`, `#docker`, `#nexus`
