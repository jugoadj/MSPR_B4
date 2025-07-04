pipeline {
    agent none // Désactivé au niveau global pour spécifier par étape

    environment {
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-creds')
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
    }

    stages {
        // Étape 1 : Checkout du code (exécuté sur n'importe quel agent)
        stage('Checkout') {
            agent any
            steps {
                git branch: 'main', 
                url: 'https://github.com/jugoadj/MSPR_B4.git'
            }
        }

        // Étape 2 : Installation des dépendances et tests (dans un conteneur Python)
        stage('Build & Test') {
            agent {
                docker {
                    image 'python:3.9-slim'
                    reuseNode true // Réutilise le workspace du checkout
                }
            }
            steps {
                sh '''
                python -m pip install --upgrade pip
                pip install -r requirements.txt pytest pytest-cov
                pytest --cov=app tests/
                '''
            }
        }

        // Étape 3 : Build de l'image Docker (dans un conteneur Docker-in-Docker)
        stage('Build Docker Image') {
            agent {
                docker {
                    image 'docker:24.0-cli'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                    reuseNode true
                }
            }
            steps {
                script {
                    docker.build(DOCKER_IMAGE)
                }
            }
        }

        // Étape 4 : Push vers Docker Hub
        stage('Push to Docker Hub') {
            agent {
                docker {
                    image 'docker:24.0-cli'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                    reuseNode true
                }
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-creds') {
                        docker.image(DOCKER_IMAGE).push()
                        docker.image(DOCKER_IMAGE).push('latest')
                    }
                }
            }
        }

        // Étape 5 : Déploiement (optionnel)
        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent any
            steps {
                sh """
                docker stop produit-ms || true
                docker rm produit-ms || true
                docker run -d \\
                    --name produit-ms \\
                    -p 8000:8000 \\
                    ${DOCKER_IMAGE}
                """
            }
        }
    }

    post {
        always {
            script {
                node('docker') {
                    cleanWs()
                    // Nettoyage sécurisé des images
                    try {
                        docker.image(DOCKER_IMAGE).remove()
                    } catch(e) {
                        echo "Cleanup skipped: ${e.message}"
                    }
                }
            }
        }
        failure {
            mail to: 'team@example.com',
            subject: "🚨 Build #${env.BUILD_NUMBER} Failed",
            body: "Check logs: ${env.BUILD_URL}"
        }
    }
}