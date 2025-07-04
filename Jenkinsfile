pipeline {
    agent any

    environment {
        // Configuration Docker Hub
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-creds')
        DOCKER_IMAGE = "jugo835/produit-ms:${env.BUILD_NUMBER}"
        
        // Configuration SonarQube
        SONAR_SCANNER_HOME = tool 'sonar-scanner'
        SONAR_PROJECT_KEY = "produit-ms"
    }  

    stages {
        // Étape 1 : Récupération du code
        stage('Checkout') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/jugoadj/MSPR_B4.git'
            }
        }

        // Étape 2 : Installation des dépendances
        stage('Install dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-cov'
            }
        }

        // Étape 3 : Exécution des tests
        stage('Run Tests') {
            steps {
                sh 'pytest --cov=app --cov-report=xml:coverage.xml tests/'
            }
            post {
                always {
                    junit 'test-reports/*.xml'  // Archive les résultats des tests
                }
            }
        }

        // Étape 4 : Analyse SonarQube
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

        // Étape 5 : Build Docker
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build(DOCKER_IMAGE)
                }
            }
        }

        // Étape 6 : Push vers Docker Hub
        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-creds') {
                        docker.image(DOCKER_IMAGE).push()
                        // Taggage supplémentaire pour 'latest' (optionnel)
                        docker.image(DOCKER_IMAGE).push('latest')
                    }
                }
            }
        }

        // Étape 7 : Déploiement (optionnel)
        stage('Deploy to Dev') {
            when {
                branch 'main'
            }
            steps {
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

    post {
        // Nettoyage après build
        always {
            cleanWs()
            script {
                // Suppression des images locales pour économiser de l'espace
                docker.image(DOCKER_IMAGE).remove()
            }
        }
        
        // Notification en cas d'échec
        failure {
            emailext (
                subject: "🚨 Échec du build #${BUILD_NUMBER}",
                body: "Le build ${BUILD_URL} a échoué",
                to: "team@example.com"
            )
        }
    }
}