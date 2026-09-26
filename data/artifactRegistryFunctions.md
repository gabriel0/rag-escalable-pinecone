# Registro de artefactos e imagenes (artifactRegistryFunctions)

Operaciones sobre imagenes Docker locales y login a registros on-prem, GCP y ECR. Tambien consulta la ultima version de un artefacto en Nexus.

## `validateContainerImageExist`

Garantiza que una imagen este presente en el daemon local. Si no esta, hace login al registro on-prem y la descarga.

### Parametros

- `aCredentialIdForRepo` (String, **Obligatorio**): ID de credencial Jenkins `UsernamePassword` del registro.
- `aRepoContainerImageWithTag` (String, **Obligatorio**): imagen con tag. El host del registro es el primer segmento separado por `/`.

### Respuesta

No retorna valor. Loguea si la imagen se descargo o si ya existia.

---

## `containerImageExistLocally`

Comprueba si `docker images` ya lista la referencia.

### Parametros

- `aContainerImageWithTag` (String, **Obligatorio**): referencia `registro/repo:tag`.

### Respuesta

`true` si `docker images -f reference=... | wc -l` es mayor a `1` (hay header mas al menos una linea). `false` en caso contrario.

Setea `env.aImageWithTag`.

---

## `retagImage`

Ejecuta `docker tag`.

### Parametros

- `currentImageTag` (String, **Obligatorio**): referencia origen.
- `newImageTag` (String, **Obligatorio**): referencia destino.

### Respuesta

No retorna valor. Setea `env.oldTag` y `env.newTag`.

---

## `removeImage`

Ejecuta `docker image rm -f`.

### Parametros

- `imageToBeRemoved` (String, **Obligatorio**): referencia a borrar.

### Respuesta

No retorna valor. Setea `env.toBeRemoved`.

---

## `uploadArtifactTo`

Publica un artefacto en el registro ya autenticado.

### Parametros

- `artifactType` (String, **Obligatorio**): tipo. Implementado: `docker` (`docker push`).
- `imagePushDestination` (String, **Obligatorio**): referencia destino del push.

### Respuesta

No retorna valor. Otro `artifactType` no ejecuta comando. Setea `env.pushDestination`.

---

## `getArtifactFrom`

Descarga un artefacto.

### Parametros

- `artifactType` (String, **Obligatorio**): tipo. Implementado: `docker` (`docker pull`).
- `imagePullDestination` (String, **Obligatorio**): referencia a descargar.

### Respuesta

No retorna valor. Otro `artifactType` no ejecuta comando. Setea `env.pullDestination`.

---

## `registryLogin`

Autentica `docker login` contra un registro y ejecuta el closure dentro de esa sesion.

### Parametros

- `aDockerRepoUrl` (String, **Obligatorio**): host del registro.
- `registryType` (String, **Obligatorio**): `onPrem`, `gcp` o `ecr`.
- `registryCredentials` (String, **Obligatorio** para `onPrem`): ID de credencial `UsernamePassword`. En `gcp` y `ecr` no se usa; el token sale de `gcloud auth print-access-token` o `aws ecr get-login-password`.
- `body` (Closure, opcional): bloque a ejecutar ya autenticado.

### Comportamiento

| `registryType` | Login |
|----------------|--------|
| `onPrem` | `docker login` con usuario y password de Jenkins |
| `gcp` | usuario `oauth2accesstoken` y access token de gcloud |
| `ecr` | usuario `AWS` y password de `aws ecr get-login-password` |

Si `body` es `null`, no hace login y loguea que no hay instrucciones.

### Respuesta

No retorna valor.

### Ejemplo

```groovy
artifactRegistryFunctions.registryLogin(dockerHost, 'onPrem', env.CREDENTIAL_NEXUS) {
    artifactRegistryFunctions.getArtifactFrom('docker', "${dockerHost}/mi-app:1.2.3")
}
artifactRegistryFunctions.retagImage("${dockerHost}/mi-app:1.2.3", "${destino}/mi-app:1.2.3")
```

---

## `latestArtifactVersion`

Consulta la API de Nexus y devuelve la version maxima del artefacto.

### Parametros

- `nexus_user`, `nexus_psw` (String, **Obligatorio**): credenciales basicas.
- `nexus_url` (String, **Obligatorio**): URL del endpoint de busqueda.
- `nexus_repository`, `nexus_group`, `nexus_artifact` (String, **Obligatorio**): coordenadas del artefacto.

### Respuesta

String con `max()` de `items[].version` del JSON. La password no se imprime (`set +x`).

**Tags:** `#docker`, `#nexus`, `#ecr`, `#gcp`
