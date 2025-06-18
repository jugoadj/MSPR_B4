pipeline {
    agent any

    environment {
        PYTHON_ENV = 'venv'
        IMAGE_NAME = 'mon-microservice-fastapi'
        DOCKER_REGISTRY = 'mon-registry.example.com'  // changer si tu utilises un registry
        DOCKER_CREDENTIALS_ID = 'docker-credentials-id'  // Jenkins credentials ID pour docker login
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                python3 -m venv $PYTHON_ENV
                source $PYTHON_ENV/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests with Coverage') {
            steps {
                sh '''
                source $PYTHON_ENV/bin/activate
                pytest --cov=app --cov-report=xml
                '''
            }
            post {
                always {
                    junit '**/test-reports/*.xml'  // si tu as des rapports junit xml
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${env.BUILD_NUMBER}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        dockerImage.push()
                        dockerImage.push('latest')
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Build & tests réussis !"
        }
        failure {
            echo "Build ou tests échoués."
        }
    }
}
