pipeline {
    agent none

    environment {
        // Configuration des images Docker
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        
        // Configuration PostgreSQL
        POSTGRES_USER = "testuser"
        POSTGRES_PASSWORD = "testpassword"
        POSTGRES_DB = "testdb"
        
        // Configuration des credentials Docker Hub
        DOCKER_CREDS = credentials('docker-hub-creds')
    }

    stages {
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

        stage('Start PostgreSQL') {
            agent any
            steps {
                script {
                    sh '''
                        docker stop test-postgres || true
                        docker rm test-postgres || true

                        docker run -d \
                        --name test-postgres \
                        -e POSTGRES_USER=${POSTGRES_USER} \
                        -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                        -e POSTGRES_DB=${POSTGRES_DB} \
                        -p 5432:5432 \
                        postgres:15

                        echo "Waiting for PostgreSQL to be ready..."
                        for i in {1..15}; do
                            docker exec test-postgres pg_isready -U ${POSTGRES_USER} && break
                            echo "PostgreSQL is not ready yet, sleeping..."
                            sleep 2
                        done

                        docker exec test-postgres pg_isready -U ${POSTGRES_USER} || \
                            (echo "PostgreSQL did not start properly." && exit 1)
                    '''
                }
            }
        }

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
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt pytest pytest-cov psycopg2-binary
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

        stage('Stop PostgreSQL') {
            agent any
            steps {
                sh '''
                    docker stop test-postgres || true
                    docker rm test-postgres || true
                '''
            }
        }

        stage('Build Docker Image') {
            agent any
            steps {
                sh """
                    docker build -t ${DOCKER_IMAGE} .
                    docker tag ${DOCKER_IMAGE} ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                """
            }
        }

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
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD} ${DOCKER_REGISTRY}
                            docker push ${DOCKER_REGISTRY}/jugo835/produit-ms:${env.BUILD_NUMBER}
                            docker push ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent any
            environment {
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@prod-postgres:5432/${POSTGRES_DB}"
            }
            steps {
                sh '''
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker network create produit-network || true
                    
                    # Démarrer PostgreSQL de production
                    docker run -d --name prod-postgres \
                        --network produit-network \
                        -e POSTGRES_USER=${POSTGRES_USER} \
                        -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                        -e POSTGRES_DB=${POSTGRES_DB} \
                        -p 5433:5432 \
                        postgres:15
                    
                    # Attendre que PostgreSQL soit prêt
                    sleep 10
                    
                    # Démarrer l'application
                    docker run -d \
                        --name produit-ms \
                        --network produit-network \
                        -p 8000:8000 \
                        -e DATABASE_URL=${DATABASE_URL} \
                        ${DOCKER_REGISTRY}/jugo835/produit-ms:latest
                '''
            }
        }
    }

    post {
        always {
            script {
                // Nettoyage des containers en cas d'échec
                sh '''
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker stop prod-postgres || true
                    docker rm prod-postgres || true
                    docker network rm produit-network || true
                '''
                // Logout Docker pour la sécurité
                sh 'docker logout || true'
            }
        }
        success {
            slackSend(color: 'good', message: "Build ${env.BUILD_NUMBER} réussi!")
        }
        failure {
            slackSend(color: 'danger', message: "Build ${env.BUILD_NUMBER} a échoué!")
        }
    }
}