# Retag de imagenes Docker (tagFunctions)

Aplica `docker tag` entre un registro/repositorio de origen y uno de destino.

## `tagImage`

Copia el tag local de una imagen hacia otra referencia. No hace push.

### Parametros

Mapa `args`:

- `sourceRegistry` (String, **Obligatorio**): host del registro origen.
- `sourceRepository` (String, **Obligatorio**): repositorio origen.
- `dockerName` (String, **Obligatorio**): nombre de la imagen origen.
- `dockerTag` (String, **Obligatorio**): tag origen.
- `targetRegistry` (String, **Obligatorio**): host del registro destino.
- `targetRepository` (String, **Obligatorio**): repositorio destino.
- `targetDockerName` (String, opcional): nombre destino. Si falta, se usa `dockerName`.
- `targetDockerTag` (String, opcional): tag destino. Si falta, se usa `dockerTag`.

Referencia resultante:

```text
{targetRegistry}/{targetRepository}/{targetDockerName|dockerName}:{targetDockerTag|dockerTag}
```

### Respuesta

No retorna valor. El comando corre con `set +x`.

### Ejemplo

```groovy
tagFunctions.tagImage([
    sourceRegistry   : env.NEXUS_DOCKER_HOST,
    sourceRepository : 'docker-local',
    dockerName       : 'mi-servicio',
    dockerTag        : env.VERSION,
    targetRegistry   : env.ECR_REGISTRY,
    targetRepository : env.ECR_REPOSITORY,
    targetDockerTag  : env.VERSION
])
```

**Tags:** `#docker`, `#tag`
