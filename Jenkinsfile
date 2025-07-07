pipeline {
    agent none

    environment {
        // Configuration Docker
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        
        // Credentials Docker Hub
        DOCKER_CREDS = credentials('docker-hub-creds')
    }

    stages {
        // Étape 1: Récupération du code
        stage('Checkout') {
            agent any
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[url: 'https://github.com/jugoadj/MSPR_B4.git']]
                ])
            }
        }

        // Étape 2: Construction et tests avec SQLite en mémoire
        stage('Build & Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root'
                    reuseNode true
                }
            }
            environment {
                DATABASE_URL = "sqlite:///:memory:"
            }
            steps {
                sh '''
                    pip install --no-cache-dir --upgrade pip
                    
                    # Forcer la désinstallation de la lib au cas où une ancienne version serait préinstallée
                    pip uninstall -y prometheus-fastapi-instrumentator || true
                    
                    # Installer toutes les dépendances avec la bonne version
                    pip install --no-cache-dir -r requirements.txt pytest pytest-cov
                    
                    pytest --cov=app --junitxml=test-results.xml -v tests/
                '''
            }

            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'test-results.xml', allowEmptyArchive: true
                }
            }
        }

        // Étape 3: Construction de l'image Docker
        stage('Build Docker Image') {
            agent any
            steps {
                sh """
                    docker build -t ${DOCKER_IMAGE} .
                    docker tag ${DOCKER_IMAGE} ${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                    docker tag ${DOCKER_IMAGE} ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                """
            }
        }

        // Étape 4: Push vers Docker Hub
        stage('Push to Docker Hub') {
            agent any
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-creds',
                        passwordVariable: 'DOCKER_PASSWORD',
                        usernameVariable: 'DOCKER_USERNAME'
                    )]) {
                        sh """
                            # Authentification
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD} ${DOCKER_REGISTRY}
                            
                            # Push des images
                            docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                            docker push ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                            
                            # Nettoyage
                            docker logout
                        """
                    }
                }
            }
        }

        // Étape 5: Déploiement en dev
        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent any
            environment {
                DATABASE_URL = "sqlite:///./prod.db"
            }
            steps {
                script {
                    sh '''
                        # Nettoyage des anciens containers
                        docker stop produit-ms || true
                        docker rm produit-ms || true
                        
                        # Lancement de l'application
                        docker run -d \
                            --name produit-ms \
                            -p 8000:8000 \
                            -e DATABASE_URL=${DATABASE_URL} \
                            ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                        
                        # Vérification que l'application répond
                        sleep 5
                        curl -f http://localhost:8000/health || \
                            (echo "Application health check failed" && exit 1)
                    '''
                }
            }
        }
        
        // Étape 6: Pull de l'image sur Docker Desktop
        stage('Pull on Docker Desktop') {
            when {
                branch 'main'
            }
            agent any
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-creds',
                        passwordVariable: 'DOCKER_PASSWORD',
                        usernameVariable: 'DOCKER_USERNAME'
                    )]) {
                        sh """
                            echo "Connexion à Docker Hub..."
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD} ${DOCKER_REGISTRY}
                            
                            echo "Pull de l'image ${DOCKER_REGISTRY}/${DOCKER_IMAGE} sur Docker Desktop..."
                            docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                            
                            echo "Déconnexion de Docker Hub..."
                            docker logout
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                node {
                    try {
                        sh '''
                        echo "Nettoyage des ressources Docker..."
                        docker stop produit-ms || echo "Le container produit-ms n'existe pas ou est déjà arrêté"
                        docker rm produit-ms || echo "Le container produit-ms n'existe pas"
                        docker logout || echo "Logout Docker non nécessaire"
                        echo "Nettoyage terminé avec succès"
                        '''
                    } catch (Exception e) {
                        echo "Erreur lors du nettoyage: ${e.message}"
                    }
                }
            }
        }
    }
}