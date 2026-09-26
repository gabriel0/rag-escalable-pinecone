# Funciones de Validacion

Esta libreria proporciona un conjunto de funciones de utilidad para validar datos, archivos de propiedades y estados de servicios antes de continuar con los procesos del pipeline. Su objetivo es asegurar la integridad de las configuraciones y prevenir errores comunes que podrian causar fallos en los despliegues.

## Metodos

### `datosProhibidos(archivo)`

Orquesta una serie de validaciones sobre un archivo de propiedades. Es la funcion principal de validacion de archivos y llama a otras funciones de validacion de forma interna.

-   **Parametros:**
    -   `archivo` (String): La ruta al archivo de propiedades a validar.
-   **Comportamiento:**
    -   Verifica que el archivo no este vacio.
    -   Valida que ninguna clave (key) comience con un numero.
    -   Asegura que no haya lineas vacias o saltos de linea extra.
    -   Llama internamente a `espaciosKeyValue(archivo)` para validar que no haya espacios alrededor del signo `=`.
    -   Llama internamente a `duplicateKey(archivo)` para asegurar que no haya claves duplicadas.
-   **Respuesta:**
    -   Si alguna validacion falla, aborta el pipeline con un mensaje de error descriptivo.

---

### `duplicateKey(archivo)`

Verifica si un archivo de propiedades contiene claves duplicadas.

-   **Parametros:**
    -   `archivo` (String): La ruta al archivo a verificar.
-   **Respuesta:**
    -   Si encuentra una clave duplicada, aborta el pipeline.

---

### `espaciosKeyValue(archivo)`

Valida que no existan espacios antes o despues del signo `=` en las asignaciones de clave-valor.

-   **Parametros:**
    -   `archivo` (String): La ruta al archivo a verificar.
-   **Respuesta:**
    -   Si encuentra espacios invalidos, aborta el pipeline.

---

### `nullData(valueP)`

Comprueba si una variable es nula, esta vacia, o contiene la cadena `"null"`.

-   **Parametros:**
    -   `valueP` (String): El valor de la variable a comprobar.
-   **Respuesta:**
    -   Si la variable es nula o invalida, aborta el pipeline.

---

### `validarStatusUrl(url)`

Verifica si una URL es accesible y responde con un codigo de estado HTTP 200. Realiza hasta 5 reintentos con un intervalo de 12 segundos si la URL no responde correctamente.

-   **Parametros:**
    -   `url` (String): La URL a validar.
-   **Respuesta:**
    -   Si despues de los reintentos la URL no responde con 200, aborta el pipeline.

---

### `invalidData(input)`

Valida que una cadena de texto contenga unicamente caracteres alfanumericos en minuscula y guiones (`-`). Tambien debe empezar y terminar con un caracter alfanumerico. Es util para validar nombres de recursos de Kubernetes.

-   **Parametros:**
    -   `input` (String): La cadena a validar.
-   **Respuesta:**
    -   Si la cadena contiene caracteres no permitidos, aborta el pipeline.

## Ejemplos de Uso

Estas funciones se suelen llamar desde un pipeline de Jenkins para garantizar la calidad de las configuraciones antes de proceder con un build o despliegue.

```groovy
// En un Jenkinsfile o libreria compartida

stage ("Validacion de Archivos") {
    steps {
        script {
            // Validar un archivo de configuraciones
            validateFunctions.datosProhibidos("configuraciones/dev.properties")

            // Validar un archivo de secretos
            validateFunctions.duplicateKey("secretos/prod.properties")
        }
    }
}

stage ("Validacion de Variables") {
    steps {
        script {
            // Validar que una variable de entorno no sea nula
            validateFunctions.nullData(env.ARTIFACT_ID)

            // Validar que un nombre de recurso sea valido para Kubernetes
            validateFunctions.invalidData(env.APP_NAME)
        }
    }
}
```

**Tags:** `#validate`, `#properties`, `#pipeline`