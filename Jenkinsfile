pipeline {
    agent none

    environment {
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        POSTGRES_USER = "testuser"
        POSTGRES_PASSWORD = "testpassword"
        POSTGRES_DB = "testdb"
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
                sh '''
                    docker stop test-postgres || true
                '''
            }
        }

        stage('Build Docker Images') {
            agent any  // <-- Important, il faut un agent ici
            steps {
                sh "docker build -t my-backend ."
            }
        }

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
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-hub-creds') {
                        docker.image(DOCKER_IMAGE).push()
                        docker.image(DOCKER_IMAGE).push('latest')
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
                DATABASE_URL = "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
                DOCKER_HOST = "unix:///var/run/docker.sock"
            }
            steps {
                sh '''
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker run -d \
                        --name produit-ms \
                        -p 8000:8000 \
                        -e DATABASE_URL=${DATABASE_URL} \
                        ${DOCKER_IMAGE}
                '''
            }
        }
    }

    
}
