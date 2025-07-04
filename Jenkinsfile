pipeline {
    agent none

    environment {
        DOCKER_IMAGE = "jugo835/produit-ms:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            agent any
            steps {
                git branch: 'main',
                    url: 'https://github.com/jugoadj/MSPR_B4.git'
            }
        }

        stage('Build & Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root'  // 👈 exécute en tant que root
                    reuseNode true
                }
            }
            steps {
                sh '''
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt pytest pytest-cov
                    pytest --cov=app tests/
                '''
            }
        }

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
                    sh "docker build -t ${DOCKER_IMAGE} ."
                }
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
            environment {
                DOCKER_HUB_CREDS = credentials('docker-hub-creds')
            }
            steps {
                script {
                    sh "echo ${DOCKER_HUB_CREDS_PSW} | docker login -u ${DOCKER_HUB_CREDS_USR} --password-stdin"
                    sh "docker push ${DOCKER_IMAGE}"
                    sh "docker tag ${DOCKER_IMAGE} jugo835/produit-ms:latest"
                    sh "docker push jugo835/produit-ms:latest"
                }
            }
        }

        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            agent {
                label 'docker' // assure-toi que ce noeud peut exécuter Docker
            }
            steps {
                sh '''
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker run -d \
                        --name produit-ms \
                        -p 8000:8000 \
                        ${DOCKER_IMAGE}
                '''
            }
        }
    }

    post {
        always {
            agent {
                label 'docker'
            }
            steps {
                cleanWs()
                script {
                    try {
                        sh "docker rmi ${DOCKER_IMAGE} || true"
                        sh "docker rmi jugo835/produit-ms:latest || true"
                    } catch (err) {
                        echo "Image cleanup skipped: ${err}"
                    }
                }
            }
        }
        failure {
            mail to: 'team@example.com',
                 subject: "🚨 Build #${BUILD_NUMBER} Failed",
                 body: "Check logs: ${BUILD_URL}"
        }
    }
}
