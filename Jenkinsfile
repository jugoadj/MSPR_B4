pipeline {
    agent any

    environment {
        // Configuration Docker Hub
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-creds')
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
    }

    stages {
        // Étape 1 : Récupération du code
        stage('Checkout') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/jugoadj/MSPR_B4.git'
            }
        }

        // Étape 2 : Installation des dépendances
        stage('Install dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov'
            }
        }

        // Étape 3 : Exécution des tests (optionnel)
        stage('Run Tests') {
            steps {
                sh 'pytest --cov=app tests/'
            }
        }

        // Étape 4 : Build Docker (avec agent dédié)
        stage('Build Docker Image') {
            agent {
                docker {
                    image 'docker:latest'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                script {
                    docker.build(DOCKER_IMAGE)
                }
            }
        }

        // Étape 5 : Push vers Docker Hub
        stage('Push to Docker Hub') {
            agent {
                docker {
                    image 'docker:latest'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-creds') {
                        docker.image(DOCKER_IMAGE).push()
                        // Tag supplémentaire 'latest' (optionnel)
                        docker.image(DOCKER_IMAGE).push('latest')
                    }
                }
            }
        }

        // Étape 6 : Déploiement (optionnel)
        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
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
                node {
                    cleanWs()  // Nettoyage du workspace
                    // Suppression propre de l'image locale
                    try {
                        docker.image(DOCKER_IMAGE).remove()
                    } catch(e) {
                        echo "Nettoyage Docker ignoré : ${e.message}"
                    }
                }
            }
        }
        failure {
            mail to: 'team@example.com',
            subject: "🚨 Échec du build #${env.BUILD_NUMBER}",
            body: "Consulter les logs : ${env.BUILD_URL}"
        }
    }
}