# Inventario de herramientas (inventoryFunctions)

Recolecta la version instalada de herramientas de plataforma, la compara contra [endoflife.date](https://endoflife.date) y publica el resultado en InfluxDB.

El entrypoint de la shared library es `call`. El resto de metodos son internos (`private`) y no se invocan desde el pipeline.

## `call`

Orquesta el inventario de un conjunto de herramientas. Por cada herramienta abre un stage, consulta EOL una sola vez, recorre los hosts, obtiene la version instalada y envia una metrica a InfluxDB.

### Parametros

- `script` (Script, **Obligatorio**): Referencia al script del pipeline (`this`). Se usa para `stage`, `echo`, `sh` y `readJSON`.
- `params` (Map, **Obligatorio**):
  - `tools` (Map): clave = nombre de la herramienta en endoflife.date; valor = mapa con `hosts` (URLs o hostnames separados por espacio) y `type` (`lts` u otro ciclo).
  - `influxParams` (Map): `bucket`, `orgId`, `token`, `url`.
  - `timeout` (int): timeout en segundos de las llamadas HTTP.

### Herramientas soportadas

| Clave | Origen de la version instalada |
|-------|--------------------------------|
| `gitlab` | `GET {host}/api/v4/version` (header `PRIVATE-TOKEN` desde `GITLAB_TOKEN`) |
| `sonarqube-server` / `sonarqube-community` | `GET {host}/api/server/version` |
| `prometheus` | `GET {host}/api/v1/status/buildinfo` |
| `nexus` | HTML de `{host}`, patron `app.js?_v=` |
| `grafana` | `GET https://{host}.example.com/api/health` |
| `jenkins` | Header `X-Jenkins` de `https://{host}.example.com:8443` |
| `mobsf` | HTML de `{host}/about` |
| `influxdb` | `GET {host}/health` (se quita el prefijo `v`) |
| `portainer` | `GET {host}/api/system/status` |
| `docker-engine` | HTML de `{host}/docker/` (cAdvisor) |

Si no hay datos de EOL, `version_internet` y `eol_internet` quedan en `N/A` y el host se registra igual. Si no se obtiene la version instalada, ese host se omite.

### Metrica en InfluxDB

Measurement `devops_inventory`. Tags: `tool_name`, `ambiente` (`test` si el host contiene `test`, si no `prod`), `servername`.

Campos: `app_version`, `version_internet`, `eol`, `eol_installed`, `status`.

`status`: `1` vigente, `2` vencido (`eol_installed=true`), `3` sin dato (`N/A`).

Respuesta HTTP esperada del write: `204`. Otro codigo se registra como advertencia y no aborta el pipeline.

### Variables de entorno

- `GITLAB_TOKEN` (**Obligatorio** solo para `gitlab`).

### Ejemplo de uso

```groovy
stage('Inventario') {
    steps {
        script {
            inventoryFunctions(this, [
                timeout: 30,
                influxParams: [
                    url   : env.INFLUX_URL,
                    orgId : env.INFLUX_ORG,
                    bucket: env.INFLUX_BUCKET,
                    token : env.INFLUX_TOKEN
                ],
                tools: [
                    jenkins: [hosts: 'jenkins-prod jenkins-test', type: 'lts'],
                    nexus  : [hosts: 'https://nexus.ejemplo', type: 'latest']
                ]
            ])
        }
    }
}
```

---

## Metodos internos

No forman parte de la API publica.

- `getInstalledVersion`: version instalada segun la herramienta. Ante error retorna `null`.
- `postToInflux`: arma el line protocol y hace `POST` a `/api/v2/write`.
- `getEolData`: `GET https://endoflife.date/api/{tool}.json`. Retorna la lista JSON o `null` si el HTTP no es `200`.
- `getCycle`: ciclo `lts` o el primer ciclo no LTS.
- `getLatestVersionFromData` / `getEolFromData`: `latest` y `eol` del ciclo, o `N/A`.
- `compareVersions`: compara versiones tipo semver. Negativo si `v1 < v2`, `0` si iguales, positivo si `v1 > v2`. `N/A` o vacio retorna `0`.
- `getInstalledEolFromData`: busca el ciclo por `major.minor` y, si no existe, por `major`. Retorna `"true"`, `"false"` o `"N/A"`.
- `isEolReached`: interpreta el campo `eol` de la API v0 (`false`, `true` o fecha `yyyy-MM-dd`). Fecha no parseable se trata como EOL (`"true"`).

**Tags:** `#inventario`, `#influx`, `#eol`
