pipeline {
    agent none

    environment {
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = "docker.io"
        DATABASE_URL = "sqlite:///:memory:"  // Définition globale
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

        stage('Build & Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    args '-u root --network=host'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt pytest pytest-cov
                    pytest --cov=app --junitxml=test-results.xml tests/
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Build Docker Image') {
            agent {
                docker {
                    image 'docker:24.0-cli'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --network=host'
                    reuseNode true
                }
            }
            steps {
                script {
                    docker.build(DOCKER_IMAGE)
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
                DOCKER_HOST = "unix:///var/run/docker.sock"
            }
            steps {
                sh """
                    docker stop produit-ms || true
                    docker rm produit-ms || true
                    docker run -d \\
                        --name produit-ms \\
                        -p 8000:8000 \\
                        -e DATABASE_URL=${DATABASE_URL} \\
                        ${DOCKER_IMAGE}
                """
            }
        }
    }

    post {
        always {
            agent any
            steps {
                cleanWs()
                script {
                    try {
                        sh "docker system prune -f"
                    } catch(err) {
                        echo "Cleanup error: ${err.message}"
                    }
                }
            }
        }
        failure {
            emailext(
                subject: "🚨 Échec du build #${env.BUILD_NUMBER}",
                body: """
                <p>Build ${env.JOB_NAME} #${env.BUILD_NUMBER} a échoué.</p>
                <p>Consultez les logs: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                """,
                to: 'adjoudjugo@gmail.com',
                mimeType: 'text/html'
            )
        }
    }
}