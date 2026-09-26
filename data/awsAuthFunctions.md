# Autenticacion AWS (awsAuthFunctions)

Configura credenciales de AWS CLI dentro de la imagen `docker-agents/aws-kubectl-kustomize` y valida la identidad con STS.

## `login`

Entra al contenedor de AWS, carga credenciales y ejecuta el bloque del pipeline ya autenticado.

### Parametros

- `credentialId` (String, **Obligatorio**): ID de credencial Jenkins `AmazonWebServicesCredentialsBinding`.
- `anAwsRegion` (String, **Obligatorio**): se exporta como `AWS_REGION` dentro del contenedor. Tambien queda en `env.awsRegion`.
- `body` (Closure, opcional): pasos a correr con la sesion activa. Si es `null`, solo deja configurado el login.

Imagen: `registry.example.com:8083/docker-agents/aws-kubectl-kustomize`.

### Respuesta

No retorna valor.

### Ejemplo

```groovy
awsAuthFunctions.login(env.SERVICE_CREDS, env.AWS_REGION) {
    awsStepFunctions.deployStepFunction([
        aStepFunctionName  : 'mi-state-machine',
        aDefinitionFilePath: 'mi-repo-1.0.0.json',
        anAwsRegion        : env.AWS_REGION
    ])
}
```

---

## `setLoginCredentials`

Escribe access key y secret key en `aws configure` y comprueba el login.

### Parametros

- `credentialId` (String, **Obligatorio**). Queda en `env.credential`.

### Respuesta

No retorna valor. Las keys no se imprimen (`set +x`).

Si `awsSuccessfulLogin` retorna `false`, marca el build `ABORTED` y falla con `AWS login failed`.

---

## `awsSuccessfulLogin`

Ejecuta `aws sts get-caller-identity`.

### Parametros

Ninguno. Usa las credenciales ya configuradas en el proceso.

### Respuesta

- `true` si STS responde. Imprime el JSON del caller.
- `false` si la llamada lanza excepcion. Loguea `Warning - Unable to validate AWS Login` y no relanza.

**Tags:** `#aws`, `#auth`
