# liquibaseFunctions

Biblioteca de funciones para gestionar migraciones de bases de datos utilizando Liquibase.

## Descripcion

Este conjunto de funciones proporciona utilidades para automatizar la ejecucion de migraciones de bases de datos mediante Liquibase, incluyendo validacion de scripts SQL, generacion automatica de changelogs, gestion de multiples bases de datos y aplicacion de cambios de esquema.

---

## Funciones Principales

### initLiquibase

Inicializa y ejecuta el proceso de migracion de Liquibase para una base de datos individual.

#### Descripcion

Funcion principal para ejecutar migraciones en una base de datos unica. Valida scripts SQL, genera el changelog XML, configura propiedades y ejecuta Liquibase.

#### Variables de Entorno Requeridas

| Variable | Descripcion |
|----------|-------------|
| `DB` | Nombre de la base de datos |
| `ENVIRONMENT` | Ambiente de despliegue (dev, pre, prod) |
| `VERSION` | Version de la migracion |
| `DATABASE_URL` | URL de conexion a la base de datos |
| `DB_USERNAME` | Usuario de base de datos |
| `DB_PASSWORD` | Contraseña de base de datos |
| `DB_SCHEMA_LIQUIBASE` | Schema donde se almacenan tablas de control de Liquibase |
| `DB_LIQUIBASE_CHANGELOGTABLE` | Nombre de tabla de changelog |
| `DB_LIQUIBASE_CHANGELOCKTABLE` | Nombre de tabla de lock |

#### Proceso de Ejecucion

1. Configura propiedades de Liquibase en archivo `liquibase.properties`
2. Construye ruta de trabajo: `./${DB}/${ENVIRONMENT}/${VERSION}`
3. Valida archivos SQL en el directorio
4. Genera archivo `changelog.xml` automaticamente
5. Ejecuta Liquibase:
   - `updateSql`: Visualiza cambios a aplicar
   - `update`: Aplica cambios en la base de datos

#### Ejemplo

```groovy
stage('Deploy Database') {
    environment {
        DB = 'mi_base_datos'
        ENVIRONMENT = 'production'
        VERSION = '1.0.0'
        DATABASE_URL = 'jdbc:mysql://db.example.com:3306/miapp'
        DB_USERNAME = 'admin'
        DB_PASSWORD = credentials('db-password')
        DB_SCHEMA_LIQUIBASE = 'liquibase'
        DB_LIQUIBASE_CHANGELOGTABLE = 'databasechangelog'
        DB_LIQUIBASE_CHANGELOCKTABLE = 'databasechangeloglock'
    }
    steps {
        script {
            liquibaseFunctions.initLiquibase()
        }
    }
}
```

#### Estructura de Directorios

```
.
└── ${DB}/
    └── ${ENVIRONMENT}/
        └── ${VERSION}/
            ├── 001_tabla_usuarios.sql
            ├── 002_tabla_permisos.sql
            └── 003_tabla_roles.sql
```

---

### ejecucionLiquibaseMultipleBase

Ejecuta migraciones de Liquibase para multiples bases de datos.

#### Descripcion

Funcion orquestadora que permite migrar multiples bases de datos en una sola ejecucion, util para ambientes con arquitectura multi-database.

#### Variables de Entorno Requeridas

| Variable | Descripcion |
|----------|-------------|
| `DIR_PREFIX_DBS` | Prefijo del directorio raiz de bases de datos (ej: "databases") |
| `ENVIRONMENT` | Ambiente (dev, pre, prod) |
| `VERSION` | Version de migracion |
| `DATABASE_URL` | URL base de conexion |
| `DB_USERNAME` | Usuario de base de datos |
| `DB_PASSWORD` | Contraseña de base de datos |
| `DB_MULTIPLE` | "si"/"no" - Si "no", usa la misma URL para todas las DBs |
| `DB_SCHEMA_LIQUIBASE` | Schema de Liquibase |
| `DB_LIQUIBASE_CHANGELOGTABLE` | Tabla de changelog |
| `DB_LIQUIBASE_CHANGELOCKTABLE` | Tabla de lock |

#### Proceso de Ejecucion

1. Busca directorios que coincidan con patron: `${DIR_PREFIX_DBS}/**/${ENVIRONMENT}/${VERSION}/`
2. Para cada directorio encontrado:
   - Extrae nombre de base de datos
   - Valida scripts SQL
   - Genera changelog.xml
   - Construye URL de conexion (si `DB_MULTIPLE=si`, añade nombre de DB a URL)
   - Ejecuta Liquibase

#### Manejo de Errores

Si una migracion falla, la funcion continua procesando las demas bases de datos y reporta el error al final.

#### Ejemplo

```groovy
stage('Deploy Multiple Databases') {
    environment {
        DIR_PREFIX_DBS = 'databases'
        ENVIRONMENT = 'production'
        VERSION = '2.0.0'
        DATABASE_URL = 'jdbc:mysql://db.example.com:3306'
        DB_USERNAME = 'admin'
        DB_PASSWORD = credentials('db-password')
        DB_MULTIPLE = 'si'
        DB_SCHEMA_LIQUIBASE = 'liquibase'
        DB_LIQUIBASE_CHANGELOGTABLE = 'databasechangelog'
        DB_LIQUIBASE_CHANGELOCKTABLE = 'databasechangeloglock'
    }
    steps {
        script {
            liquibaseFunctions.ejecucionLiquibaseMultipleBase()
        }
    }
}
```

#### Estructura de Directorios Esperada

```
.
└── databases/
    ├── usuarios_db/
    │   └── production/
    │       └── 2.0.0/
    │           ├── 001_tabla_usuarios.sql
    │           └── 002_tabla_permisos.sql
    ├── productos_db/
    │   └── production/
    │       └── 2.0.0/
    │           ├── 001_tabla_productos.sql
    │           └── 002_tabla_categorias.sql
    └── pedidos_db/
        └── production/
            └── 2.0.0/
                ├── 001_tabla_pedidos.sql
                └── 002_tabla_items.sql
```

#### Busqueda de Directorios

El comando de busqueda utilizado:

```bash
find . -type d -path './databases' ! -path './.git*' ! -path './jenkins*' -printf '%P\n' | grep ${VERSION} | grep ${ENVIRONMENT}
```

Esto busca directorios que cumplan:
- Prefijo: `databases`
- Excluye: `.git*` y `jenkins*`
- Contienen: `${ENVIRONMENT}` y `${VERSION}` en la ruta

---

## Funciones Auxiliares

### ejecucionLiquibase

Ejecuta los comandos de Liquibase (updateSql y update).

#### Variables Requeridas

| Variable | Descripcion |
|----------|-------------|
| `STRING_DATABASE_URL` | URL de conexion a la base de datos |

#### Comandos Ejecutados

1. **updateSql**: Genera SQL que sera ejecutado
   ```bash
   liquibase --url=${STRING_DATABASE_URL} updateSql
   ```
   - Muestra los cambios a aplicar sin modificar la BD
   - Util para revision antes de aplicar

2. **update**: Aplica los cambios
   ```bash
   liquibase --url=${STRING_DATABASE_URL} update
   ```
   - Ejecuta los cambios pendientes
   - Registra cambios en tabla de changelog

#### Ejemplo

```groovy
env.STRING_DATABASE_URL = 'jdbc:mysql://db.example.com:3306/miapp'
liquibaseFunctions.ejecucionLiquibase()
```

---

### validarArchivosSQL

Valida que los scripts SQL no contengan comandos DDL no permitidos.

#### Descripcion

Previene la ejecucion de scripts SQL que contienen comandos DDL potencialmente peligrosos para bases de datos de produccion.

#### Comandos No Permitidos

Se bloquean scripts que contengan (case-insensitive):

- `CREATE DATABASE`
- `CREATE SCHEMA`
- `DROP DATABASE`
- `DROP SCHEMA`
- `ALTER DATABASE`
- `ALTER SCHEMA`
- `DROP TABLE`
- `DROP VIEW`
- `DROP SEQUENCE`
- `DROP FUNCTION`
- `DROP PROCEDURE`
- `DROP COLUMN`
- `DROP CONSTRAINT`
- `DROP INDEX`
- `RENAME DATABASE`
- `RENAME SCHEMA`
- `RENAME TABLE`
- `RENAME COLUMN`

#### Parametros

| Nombre | Tipo | Descripcion |
|--------|------|-------------|
| directorio | String | Ruta donde se encuentran los archivos SQL a validar |

#### Expresion Regular Utilizada

```
'^\\s*(CREATE|ALTER|DROP|RENAME)\\s+(DATABASE|SCHEMA|TABLE|VIEW|SEQUENCE|FUNCTION|PROCEDURE|COLUMN|CONSTRAINT|INDEX)\\b'
```

#### Comportamiento

- Si encuentra comandos no permitidos: **Detiene la ejecucion con error**
- Si no encuentra problemas: **Continua sin problemas**

#### Ejemplo

```groovy
// Esto generara error (DROP TABLE no permitido)
liquibaseFunctions.validarArchivosSQL('./databases/usuarios/production/1.0.0')

// En archivos:
// 001_tabla_usuarios.sql contiene: DROP TABLE usuarios;
// Error: "Scripts SQL no permitidos encontrados en ./databases/usuarios/production/1.0.0"
```

#### Scripts Validos

```sql
-- ✓ VALIDO: Crear columna nueva
ALTER TABLE usuarios ADD COLUMN fecha_registro TIMESTAMP;

-- ✓ VALIDO: Crear vista
CREATE VIEW usuarios_activos AS SELECT * FROM usuarios WHERE estado = 'activo';

-- ✓ VALIDO: Crear indice
CREATE INDEX idx_email ON usuarios(email);

-- ✓ VALIDO: Insertar datos
INSERT INTO usuarios (nombre, email) VALUES ('Juan', 'usuario.ejemplo');

-- ✓ VALIDO: Actualizar datos
UPDATE usuarios SET fecha_registro = NOW() WHERE id > 0;
```

#### Scripts No Validos

```sql
-- ✗ NO PERMITIDO: Eliminar tabla
DROP TABLE usuarios;

-- ✗ NO PERMITIDO: Eliminar base de datos
DROP DATABASE miapp;

-- ✗ NO PERMITIDO: Renombrar tabla
RENAME TABLE usuarios TO usuarios_backup;

-- ✗ NO PERMITIDO: Eliminar esquema
DROP SCHEMA public;
```

---

### escribirChangelogXML

Genera automaticamente el archivo `changelog.xml` de Liquibase.

#### Descripcion

Crea un archivo XML de Liquibase que incluye todos los scripts SQL de un directorio especifico.

#### Parametros

| Nombre | Tipo | Descripcion |
|--------|------|-------------|
| directorio | String | Ruta de los scripts SQL a incluir |

#### Archivo Generado

**Nombre**: `changelog.xml`

**Ubicacion**: Directorio actual de ejecucion

**Contenido**:

```xml
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:ext="http://www.liquibase.org/xml/ns/dbchangelog-ext"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-2.0.xsd
    http://www.liquibase.org/xml/ns/dbchangelog-ext http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-ext.xsd">

    <includeAll path="${directorio}"/>
</databaseChangeLog>
```

#### Caracteristicas

- Incluye **todos los archivos** del directorio especificado
- Los archivos se procesan en **orden alfabetico**
- Soporta archivos `.sql` y `.xml`
- Automaticamente generado (no requiere mantenimiento manual)

#### Ejemplo

```groovy
liquibaseFunctions.escribirChangelogXML('./databases/usuarios/production/1.0.0')

// Genera archivo changelog.xml que incluye:
// - ./databases/usuarios/production/1.0.0/001_tabla_usuarios.sql
// - ./databases/usuarios/production/1.0.0/002_tabla_permisos.sql
// - ./databases/usuarios/production/1.0.0/003_tabla_roles.sql
```

---

### escribirLiquibaseProperties

Genera el archivo de configuracion `liquibase.properties`.

#### Descripcion

Crea el archivo de propiedades requerido por Liquibase con credenciales y configuraciones de base de datos.

#### Archivo Generado

**Nombre**: `liquibase.properties`

**Ubicacion**: Directorio actual de ejecucion

#### Propiedades Configuradas

| Propiedad | Variable de Entorno | Descripcion |
|-----------|------------------|-------------|
| `changeLogFile` | (fija) | Ruta del archivo changelog: `changelog.xml` |
| `username` | `DB_USERNAME` | Usuario de autenticacion en BD |
| `password` | `DB_PASSWORD` | Contraseña de autenticacion en BD |
| `liquibase.liquibaseSchemaName` | `DB_SCHEMA_LIQUIBASE` | Schema donde se guardan tablas de control |
| `liquibase.databaseChangeLogTableName` | `DB_LIQUIBASE_CHANGELOGTABLE` | Tabla que registra cambios aplicados |
| `liquibase.databaseChangeLogLockTableName` | `DB_LIQUIBASE_CHANGELOCKTABLE` | Tabla que controla locks durante migraciones |

#### Variables de Entorno Requeridas

| Variable | Descripcion |
|----------|-------------|
| `DB_USERNAME` | Usuario de base de datos |
| `DB_PASSWORD` | Contraseña de base de datos |
| `DB_SCHEMA_LIQUIBASE` | Schema de Liquibase |
| `DB_LIQUIBASE_CHANGELOGTABLE` | Nombre de tabla de changelog |
| `DB_LIQUIBASE_CHANGELOCKTABLE` | Nombre de tabla de lock |

#### Contenido Generado

```properties
changeLogFile=changelog.xml
username=admin
password=mypassword
liquibase.liquibaseSchemaName=liquibase
liquibase.databaseChangeLogTableName=databasechangelog
liquibase.databaseChangeLogLockTableName=databasechangeloglock
```

#### Seguridad

- La contraseña se escribe en el archivo (considera usar credenciales encriptadas)
- El archivo debe protegerse ya que contiene credenciales de base de datos
- Usar Jenkins credentials en lugar de valores hardcodeados

#### Ejemplo

```groovy
env.DB_USERNAME = 'admin'
env.DB_PASSWORD = credentials('database-password')
env.DB_SCHEMA_LIQUIBASE = 'liquibase'
env.DB_LIQUIBASE_CHANGELOGTABLE = 'databasechangelog'
env.DB_LIQUIBASE_CHANGELOCKTABLE = 'databasechangeloglock'

liquibaseFunctions.escribirLiquibaseProperties()
// Genera: liquibase.properties
```

---

### setWriteLiquibaseProperties

Genera `liquibase.properties` con el juego de variables `*_RL`. No lo llama `initLiquibase` ni `ejecucionLiquibaseMultipleBase`; esas rutas usan `escribirLiquibaseProperties`.

#### Archivo generado

`liquibase.properties` en el directorio de ejecucion. No incluye `liquibase.liquibaseSchemaName`.

#### Propiedades

| Propiedad | Variable de entorno |
|-----------|---------------------|
| `username` | `DB_USERNAME_RL` |
| `password` | `DB_PASSWORD_RL` |
| `changeLogFile` | `${DB_VOLUMEN_PATH_RL}${DB_CHANGELOGFILE_RL}` |
| `liquibase.databaseChangeLogTableName` | `DB_LIQUIBASE_CHANGELOGTABLE_RL` |
| `liquibase.databaseChangeLogLockTableName` | `DB_LIQUIBASE_CHANGELOCKTABLE_RL` |

#### Retorna

No retorna valor.

#### Ejemplo

```groovy
liquibaseFunctions.setWriteLiquibaseProperties()
```

---

## Ejemplo Completo de Pipeline

### Para Base de Datos Simple

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        DB = 'usuarios_db'
        ENVIRONMENT = 'production'
        VERSION = '1.0.0'
        DATABASE_URL = 'jdbc:mysql://db.example.com:3306/usuarios_app'
        DB_USERNAME = credentials('db-username')
        DB_PASSWORD = credentials('db-password')
        DB_SCHEMA_LIQUIBASE = 'liquibase'
        DB_LIQUIBASE_CHANGELOGTABLE = 'databasechangelog'
        DB_LIQUIBASE_CHANGELOCKTABLE = 'databasechangeloglock'
    }

    stages {
        stage('Prepare') {
            steps {
                script {
                    echo "Preparando migracion para: ${DB}"
                    echo "Version: ${VERSION}"
                    echo "Ambiente: ${ENVIRONMENT}"
                }
            }
        }

        stage('Migrate Database') {
            steps {
                script {
                    try {
                        liquibaseFunctions.initLiquibase()
                        echo "Migracion completada exitosamente"
                    } catch (Exception e) {
                        echo "Error en migracion: ${e.message}"
                        throw e
                    }
                }
            }
        }

        stage('Verify') {
            steps {
                script {
                    sh """
                        echo "Verificando estado de Liquibase..."
                        liquibase --url=${DATABASE_URL} history
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Migracion completada: ${DB} v${VERSION}"
        }
        failure {
            echo "Migracion fallo: ${DB}"
        }
    }
}
```

### Para Multiples Bases de Datos

```groovy
@Library('devops-library-commons') _

pipeline {
    agent any

    environment {
        DIR_PREFIX_DBS = 'databases'
        ENVIRONMENT = 'production'
        VERSION = '2.0.0'
        DATABASE_URL = 'jdbc:mysql://db.example.com:3306'
        DB_USERNAME = credentials('db-username')
        DB_PASSWORD = credentials('db-password')
        DB_MULTIPLE = 'si'
        DB_SCHEMA_LIQUIBASE = 'liquibase'
        DB_LIQUIBASE_CHANGELOGTABLE = 'databasechangelog'
        DB_LIQUIBASE_CHANGELOCKTABLE = 'databasechangeloglock'
    }

    stages {
        stage('Prepare') {
            steps {
                script {
                    echo "Preparando migraciones multiples"
                    echo "Version: ${VERSION}"
                    echo "Ambiente: ${ENVIRONMENT}"
                }
            }
        }

        stage('Migrate All Databases') {
            steps {
                script {
                    try {
                        liquibaseFunctions.ejecucionLiquibaseMultipleBase()
                        echo "Todas las migraciones completadas"
                    } catch (Exception e) {
                        echo "Error en migraciones: ${e.message}"
                        throw e
                    }
                }
            }
        }

        stage('Post Migration Verification') {
            steps {
                script {
                    sh """
                        echo "Migraciones completadas exitosamente"
                        echo "Verificar tablas databasechangelog en cada base de datos"
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Todas las migraciones completadas: v${VERSION}"
        }
        failure {
            echo "Fallo en migraciones multiples"
        }
    }
}
```

---

## Notas Importantes

### Prerequisitos

- **Liquibase**: Instalado en el agente de Jenkins
- **JDBC Driver**: Controlador apropiado para el tipo de base de datos (MySQL, PostgreSQL, Oracle, etc.)
- **Permisos**: Usuario de BD debe tener permisos DDL/DML
- **Conectividad**: Acceso de red a los servidores de base de datos

### Estructura de Scripts SQL

#### Nomenclatura Recomendada

```
001_tabla_usuarios.sql
002_tabla_permisos.sql
003_tabla_roles.sql
004_agregar_indice_email.sql
005_insertar_datos_iniciales.sql
```

#### Contenido Recomendado

```sql
-- Cambio 1: Crear tabla usuarios
-- Descripcion: Tabla para almacenar usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    estado VARCHAR(50) DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cambio 2: Crear indice
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
```

### Variables de URL de Base de Datos

#### MySQL

```
jdbc:mysql://host:3306/nombre_db
```

#### PostgreSQL

```
jdbc:postgresql://host:5432/nombre_db
```

#### Oracle

```
jdbc:oracle:thin:@host:1521:SID
```

#### SQL Server

```
jdbc:sqlserver://host:1433;databaseName=nombre_db
```

### Changelog XML - Explicacion

El archivo `changelog.xml` generado:

- **Incluye automaticamente** todos los scripts SQL de un directorio
- **Procesa en orden alfabetico**: 001_, 002_, 003_, etc.
- **Permite versionado**: Cada cambio es registrado con ID unico
- **Soporta rollback**: Cambios reversos si se especifican

### Tabla de Changelog de Liquibase

Liquibase crea automaticamente una tabla para registrar cambios:

```
databasechangelog table:
- ID: Identificador del cambio
- AUTHOR: Autor del cambio
- FILENAME: Archivo que contiene el cambio
- DATEEXECUTED: Fecha de ejecucion
- ORDEREXECUTED: Orden de ejecucion
- EXECTYPE: Tipo de ejecucion (EXECUTED, FAILED, SKIPPED)
- MD5SUM: Hash del contenido
- DESCRIPTION: Descripcion del cambio
- COMMENTS: Comentarios adicionales
- TAG: Tag para rollback
- LIQUIBASE: Version de Liquibase
- CONTEXTS: Contextos de ejecucion
- LABELS: Etiquetas
- DEPLOYMENT_ID: ID de despliegue
```

### Errores Comunes

#### "Schema does not exist"

**Causa**: La schema especificada en `DB_SCHEMA_LIQUIBASE` no existe

**Solucion**: Crear la schema antes de ejecutar Liquibase

```sql
CREATE SCHEMA liquibase;
```

#### "User does not have permission"

**Causa**: Usuario de base de datos no tiene permisos suficientes

**Solucion**: Otorgar permisos:

```sql
GRANT ALL PRIVILEGES ON *.* TO 'usuario'@'%';
FLUSH PRIVILEGES;
```

#### "Cannot acquire change log lock"

**Causa**: Otra migracion esta en curso o lock table esta bloqueada

**Solucion**: Esperar o limpiar tabla de lock:

```sql
DELETE FROM databasechangeloglock;
```

#### "SQL scripts with forbidden commands found"

**Causa**: Scripts contienen comandos DDL no permitidos (DROP TABLE, etc.)

**Solucion**: Revisar y eliminar comandos no permitidos, usar ALTER en lugar de DROP

---

## Dependencias

- **Liquibase CLI**: Herramienta de linea de comandos para migraciones
- **JDBC Drivers**: Para conectar a bases de datos especificas
- **Bash/Shell**: Para ejecutar comandos find y grep
- **Jenkins Credentials**: Para gestionar credenciales de base de datos

---

## Flujo de Ejecucion Tipico

```
1. initLiquibase() o ejecucionLiquibaseMultipleBase()
   ↓
2. escribirLiquibaseProperties()
   - Genera liquibase.properties con configuracion
   ↓
3. validarArchivosSQL()
   - Valida que scripts no contengan comandos prohibidos
   ↓
4. escribirChangelogXML()
   - Genera changelog.xml con includeAll
   ↓
5. ejecucionLiquibase()
   - Ejecuta updateSql (preview)
   - Ejecuta update (aplicacion real)
   ↓
6. Liquibase registra en databasechangelog
   - Tabla de control que evita re-ejecutar cambios
```

---

## Seguridad

### Contraseñas

- Usar Jenkins credentials: `credentials('credential-id')`
- Evitar hardcodear contraseñas en pipeline
- Considerar variables encriptadas

### Validacion de Scripts

- Sistema automatico bloquea comandos peligrosos (DROP, DELETE schemas)
- Requiere revision manual de cambios antes de aplicar
- `updateSql` permite inspeccionar cambios antes de aplicar

### Permisos de Base de Datos

- Usuario debe tener minimos permisos necesarios
- Separar usuarios: uno para lectura, otro para escritura
- Auditar cambios en tablas de changelog de Liquibase

---

**Tags:** `#liquibase`, `#database-migration`, `#sql`, `#devops`, `#ci-cd`, `#jenkins`, `#pipeline`, `#database`, `#ddl`, `#changelog`
