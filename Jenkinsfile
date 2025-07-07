pipeline {
    agent none

    environment {
        // Configuration Docker
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        
        // Configuration PostgreSQL
        POSTGRES_USER = "testuser"
        POSTGRES_PASSWORD = "testpassword"
        POSTGRES_DB = "testdb"
        
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

        // Étape 2: Lancement PostgreSQL pour les tests
        stage('Start Test PostgreSQL') {
            agent any
            steps {
                script {
                    sh '''
                        # Nettoyage des anciens containers
                        docker stop test-postgres || true
                        docker rm test-postgres || true

                        # Lancement du container PostgreSQL
                        docker run -d \
                            --name test-postgres \
                            -e POSTGRES_USER=${POSTGRES_USER} \
                            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                            -e POSTGRES_DB=${POSTGRES_DB} \
                            -p 5432:5432 \
                            postgres:15

                        # Attente que PostgreSQL soit prêt
                        echo "Waiting for PostgreSQL to be ready..."
                        for i in {1..15}; do
                            if docker exec test-postgres pg_isready -U ${POSTGRES_USER}; then
                                break
                            fi
                            echo "PostgreSQL is not ready yet, sleeping..."
                            sleep 2
                        done

                        # Vérification finale
                        docker exec test-postgres pg_isready -U ${POSTGRES_USER} || \
                            (echo "PostgreSQL did not start properly." && exit 1)
                    '''
                }
            }
        }

        // Étape 3: Construction et tests
        stage('🧪 Tests Unitaires') {
      steps {
        bat '''
          docker run --rm ^
            -e ORDER_DB_URL="sqlite:///:memory:" ^
            -v "%WORKSPACE%":/app ^
            -w /app ^
            python:3.11-slim ^
            sh -c "pip install --upgrade pip && \
                   pip install -r requirements.txt && \
                   pytest --maxfail=1 --disable-warnings -q --junitxml=results.xml"
        '''
      }
      post {
        always {
          junit 'results.xml'
        }
        failure {
          echo '❌ Les tests ont échoué !'
        }
      }
    }

        // Étape 4: Arrêt de PostgreSQL de test
        stage('Stop Test PostgreSQL') {
            agent any
            steps {
                sh '''
                    docker stop test-postgres || true
                    docker rm test-postgres || true
                '''
            }
        }

        // Étape 5: Construction de l'image Docker
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

        // Étape 6: Push vers Docker Hub
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


                // Étape 6.5: Pull de l'image sur Docker Desktop
        stage('Pull on Docker Desktop') {

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
                        docker stop prod-postgres || echo "Le container prod-postgres n'existe pas ou est déjà arrêté"
                        docker rm prod-postgres || echo "Le container prod-postgres n'existe pas"
                        docker network rm produit-network || echo "Le réseau produit-network n'existe pas"
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