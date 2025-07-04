pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-creds')
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        SONAR_SCANNER_HOME = tool 'sonar-scanner'
        SONAR_PROJECT_KEY = "produit-ms"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/jugoadj/MSPR_B4.git'
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest --cov=app --cov-report=xml:coverage.xml tests/'
            }
            post {
                always {
                    junit 'test-reports/*.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube-Server') {
                    sh """
                    ${SONAR_SCANNER_HOME}/bin/sonar-scanner \
                    -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                    -Dsonar.sources=app \
                    -Dsonar.language=py
                    """
                }
            }
        }

        // MODIFICATION CLAÉ : Utilisation d'un agent Docker pour les étapes Docker
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
                        docker.image(DOCKER_IMAGE).push('latest')
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            steps {
                script {
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
    }

    post {
        always {
            cleanWs()
            script {
                // MODIFICATION : Suppression conditionnelle
                try {
                    docker.image(DOCKER_IMAGE).remove()
                } catch(e) {
                    echo "Erreur lors du nettoyage : ${e.message}"
                }
            }
        }
        failure {
            emailext (
                subject: "🚨 Échec du build #${BUILD_NUMBER}",
                body: "Consultez les détails : ${env.BUILD_URL}",
                to: "team@example.com"
            )
        }
    }
}