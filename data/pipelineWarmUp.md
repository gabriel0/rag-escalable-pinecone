# Funcion para warmUp de pipelines
La idea es que exista una funcion nomenclada con el tipo de pipeline, por ejemplo si a futuro queremos hacer warmup de helm, habra un metodo principal "def helm ()" y dentro de ese metodo la logica para resolver lo necesario.

## Requisitos
**Metodos principales:**
- unificado: Se encargar de realizar una serie de actividades neesarias para que el pipeline unificado funcione.
    - Descarga el repositorio de kustomize y de configuraciones
    - Procesa las configuraciones del repositorio
    - Realiza el login a la/las registries necesarias
    - Valida si la imagen a construir ya existe, de manera que con ese dato se puedan saltear los pasos no necesarios (como construir la imagen si es que ya existe)

**Metodos secundarios:**
- N/A

## Parametros
Mapa de parametros con todas las variables necesarias para pre cargar todos los datos necesarios para el tipo de pipeline.

## Usos

Llamadas

```javascript
    pipelineWarmup.unificado()
```
**Tags:** `#pipeline-warmup`, `#unificado`