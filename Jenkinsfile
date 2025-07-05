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
        stage('Build & Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root --network=host'
                    reuseNode true
                }
            }
            environment {
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
            }
            steps {
                sh '''
                    # Installation des dépendances
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt pytest pytest-cov psycopg2-binary
                    
                    # Exécution des tests
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
                            docker push ${DOCKER_REGISTRY}/jugo835/produit-ms:${env.BUILD_NUMBER}
                            docker push ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                            
                            # Nettoyage
                            docker logout
                        """
                    }
                }
            }
        }

        // Étape 7: Déploiement en dev
        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent any
            environment {
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@prod-postgres:5432/${POSTGRES_DB}"
            }
            steps {
                script {
                    sh '''
                        # Nettoyage des anciens containers
                        docker stop produit-ms || true
                        docker rm produit-ms || true
                        docker stop prod-postgres || true
                        docker rm prod-postgres || true
                        
                        # Création du réseau
                        docker network create produit-network || true
                        
                        # Lancement de PostgreSQL de production
                        docker run -d \
                            --name prod-postgres \
                            --network produit-network \
                            -e POSTGRES_USER=${POSTGRES_USER} \
                            -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                            -e POSTGRES_DB=${POSTGRES_DB} \
                            -p 5433:5432 \
                            postgres:15
                        
                        # Attente que PostgreSQL soit prêt
                        sleep 10
                        
                        # Lancement de l'application
                        docker run -d \
                            --name produit-ms \
                            --network produit-network \
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
    }
    stage('Deploy to Docker Desktop') {
            agent any
            environment {
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@prod-postgres:5432/${POSTGRES_DB}"
            }
            steps {
                script {
                    // Cette commande SSH serait exécutée sur votre machine locale
                    // Vous devez configurer l'accès SSH entre Jenkins et votre machine
                    sshagent(['your-ssh-credentials']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no user@your-local-ip << 'ENDSSH'
                            # Arrêt des containers existants
                            docker stop produit-ms || true
                            docker rm produit-ms || true
                            docker stop prod-postgres || true
                            docker rm prod-postgres || true
                            
                            # Création du réseau
                            docker network create produit-network || true
                            
                            # Lancement de PostgreSQL
                            docker run -d \\
                                --name prod-postgres \\
                                --network produit-network \\
                                -e POSTGRES_USER=${POSTGRES_USER} \\
                                -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \\
                                -e POSTGRES_DB=${POSTGRES_DB} \\
                                -p 5433:5432 \\
                                postgres:15
                            
                            # Attente que PostgreSQL soit prêt
                            sleep 10
                            
                            # Téléchargement de la dernière image
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD} ${DOCKER_REGISTRY}
                            docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                            docker logout
                            
                            # Lancement de l'application
                            docker run -d \\
                                --name produit-ms \\
                                --network produit-network \\
                                -p 8000:8000 \\
                                -e DATABASE_URL=${DATABASE_URL} \\
                                ${DOCKER_REGISTRY}/${DOCKER_IMAGE}
                            
                            # Vérification
                            sleep 5
                            curl -f http://localhost:8000/health || \\
                                (echo "Application health check failed" && exit 1)
                            echo "Application deployed successfully to Docker Desktop!"
                            ENDSSH
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