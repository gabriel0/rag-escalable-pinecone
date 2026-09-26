# Build y empaquetado de artefactos (artifactBuildFunctions)

Compila segun lenguaje y arma el paquete final (jar o zip) a partir de reglas `origen:destino`.

## `buildArtifact`

Elige el builder segun `params.language`.

### Parametros

- `params` (Map):
  - `language`: `java_mvn`, `yarn` o `python`. Cualquier otro valor loguea que no hay builder y no falla.
  - El resto se reenvia al builder concreto.

### Respuesta

No retorna valor.

### Ejemplo

```groovy
artifactBuildFunctions.buildArtifact([
    language               : 'java_mvn',
    strategy               : 'lambda',
    runTests               : 'true',
    keepIntermediateArtifact: 'false',
    langVersion            : '17',
    dockerAgentImage       : env.DOCKER_PIPELINE_RUN
])
```

---

## `mavenArtifactBuild`

Compila un proyecto Maven dentro de la imagen `maven3-jdk`.

### Parametros obligatorios

Validados con `utilsFunctions.validateParams`:

- `strategy`, `language`, `runTests`, `keepIntermediateArtifact`, `langVersion`, `dockerAgentImage`.

Opcionales:

- `registryHost`: host de Nexus. Si falta, usa `env.NEXUS_PROXY_HOST`.
- `intermediateArtifactRepo`: repositorio de `mvn deploy` cuando `keepIntermediateArtifact=true`.

### Logica

1. Copia `../pipeline/{strategy}/{language}/settings.xml` al workspace si existe.
2. Dentro del agente Maven: `dependency:resolve-plugins`, `dependency:resolve`, `install`.
3. `mvn clean package`. Si `runTests` no es `true`, agrega `-DskipTests`.
4. Si `keepIntermediateArtifact=true`, `mvn clean deploy` al repositorio `nexus`.

### Respuesta

No retorna valor.

---

## `runYarnBuild`

Ejecuta `yarn install` y `yarn build` en la imagen fija `registry.example.com:8083/docker-agents/node22:22.2.0`.

### Parametros

- `params` (Map): no se leen campos. El log usa `params.lang` solo como texto.

### Respuesta

No retorna valor.

---

## `pythonArtifactBuild`

Instala dependencias con `pip install --target=python -r requirements.txt`.

### Parametros

- `params.dockerAgentImage` (String, **Obligatorio**): prefijo del registro de agentes.
- `params.langVersion` (String, **Obligatorio**): tag de `docker-agents/python`.

### Respuesta

No retorna valor. Requiere `requirements.txt` en el workspace.

---

## `runCustomBuild`

Ejecuta un comando arbitrario dentro de una imagen Docker.

### Parametros

- `buildCommand` (String, **Obligatorio**): comando de shell.
- `dockerImage` (String, **Obligatorio**): imagen. Vacia o en blanco aborta con `Debe especificarse una imagen Docker para builds personalizados`.

### Respuesta

No retorna valor.

---

## `packageArtifactObjects`

Arma el artefacto final en `tmpArtifactPackageDir` segun reglas de copia.

### Parametros

- `params.destPackageName` (String, **Obligatorio**): nombre de salida. La extension (`jar` o `zip`) define el cierre.
- `params.packageRules` (String, opcional): reglas separadas por coma. Cada regla es `origen:destino`.
- `params.serviceName`, `params.artifactVersion`: se usan cuando `origen` es `jar`.
- `params.appSrc`: si no hay reglas, se copia `{appSrc}/*` al directorio temporal.

### Origenes de regla

| `origen` | Accion |
|----------|--------|
| `jar` | Si hay mas de un jar en `target/`, borra `target/original*`. Copia el jar como `{destino}{serviceName}-{artifactVersion}.jar`. |
| `jars` | Copia `target/*` a `{destino}`. |
| otro path | `cp -r` del path al destino. |

Si la extension del paquete es `jar`, copia ese jar tambien a `./{destino}`. Si es `zip`, comprime el directorio temporal con `utilsFunctions.utilsZip` excluyendo `**/*.git`.

### Respuesta

No retorna valor.

---

## `preparePackagedArtifact`

Copia un artefacto que ya viene empaquetado, sin rearmar el contenido.

### Parametros

- `params.packageRules` (String, **Obligatorio**): una sola regla `origen:destino`. Mas de una regla aborta.
- `params.destPackageName` (String, **Obligatorio**): nombre del archivo destino.

### Respuesta

No retorna valor. Ante error setea `MENSAJE` a `Pipeline: Error preparando artefacto ya paquetizado` y aborta.

**Tags:** `#build`, `#maven`, `#yarn`, `#python`, `#artifact`
