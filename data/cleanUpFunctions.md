# Funcion para limpieza
- Limpieza de imagenes docker por TAG
- Limpieza de imagenes docker por LABEL

*Se pueden sumar mas funciones de limpieza que no tengan que ver con docker propiamente dicho*

## Requisitos
**Metodos principales:**

 - dockerRemoveImagesList: Es el metodo principal de la libreria, el cual intenta orquestar todos los pasos necesarios a la hora de realizar una limpieza de imagenes docker.

**Metodos secundarios:**

 - isDockerImageValid: Este metodo verifica si una imagen docker es valida o no, validando que el parametro no sea nulo, vacio, * ni %

 - dockerRemoveByName: Este metodo elimina una imagen docker por nombre.

 - dockerRemoveByLabel: Este metodo elimina una imagen docker por etiqueta.

## Parametros

## Usos
Llamada a la
```javascript
    def imageNames = [
        "stage=build_coverage_${SERVICE_NAME}_${BUILD_NUMBER}",
        "stage=coverage_${SERVICE_NAME}_${BUILD_NUMBER}",
        "stage=build_${SERVICE_NAME}_${BUILD_NUMBER}"
    ]
    cleanUpFunctions.dockerRemoveImagesList(imageNames)
```

**Tags:** `#cleanup`,`#docker`