stage('Deploy') {
            steps {
                dockerCompose(
                    stackName: 'devops-api',
                    imageName: 'nexus:port/devops-api:latest',
                    containerName: 'devops-api',
                    restart: 'always',
                    ports: ['8080:8080', '443:443'], // Puertos para verificar
                    networks: ['my-network', 'frontend-network'], // Redes personalizadas
                    envVars: [
                        MY_ENV_VAR: 'value'
                    ]
                )
            }
        }