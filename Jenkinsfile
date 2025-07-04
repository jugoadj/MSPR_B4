pipeline {
    agent none

    environment {
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        POSTGRES_USER = "testuser"
        POSTGRES_PASSWORD = "testpassword"
        POSTGRES_DB = "testdb"

        // Ces deux variables doivent être définies via les Credentials Jenkins (type : "Secret Text")
        DOCKER_HUB_USERNAME = credentials('docker-hub-username') // ID de la credential = docker-hub-username
        DOCKER_HUB_PASSWORD = credentials('docker-hub-password') // ID de la credential = docker-hub-password
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

                        docker exec test-postgres pg_isready -U ${POSTGRES_USER} || (echo "PostgreSQL did not start properly." && exit 1)
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
                }
            }
        }

        stage('Stop PostgreSQL') {
            agent any
            steps {
                sh 'docker stop test-postgres || true'
            }
        }

        stage('Build Docker Image') {
            agent any
            steps {
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }

        stage('Login & Push to Docker Hub') {
            agent any
            steps {
                sh """
                    echo "${DOCKER_HUB_PASSWORD}" | docker login -u "${DOCKER_HUB_USERNAME}" --password-stdin
                    docker tag ${DOCKER_IMAGE} jugo835/produit-ms:${BUILD_NUMBER}
                    docker tag ${DOCKER_IMAGE} jugo835/produit-ms:latest
                    docker push jugo835/produit-ms:${BUILD_NUMBER}
                    docker push jugo835/produit-ms:latest
                """
            }
        }

        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent any
            environment {
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
            }
            steps {
                sh '''
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker run -d \
                        --name produit-ms \
                        -p 8000:8000 \
                        -e DATABASE_URL=${DATABASE_URL} \
                        jugo835/produit-ms:${BUILD_NUMBER}
                '''
            }
        }
    }
}
