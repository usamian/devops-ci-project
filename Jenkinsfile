pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "atlas-ai-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONARQUBE_URL = "http://sonarqube:9000"
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo "Pulling code from repository..."
                checkout scm
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                echo "Running code quality analysis..."
                withSonarQubeEnv('sonarqube-server') {
                    sh '''
                    sonar-scanner \
                      -Dsonar.projectKey=atlas-ai \
                      -Dsonar.sources=src/ \
                      -Dsonar.host.url=http://sonarqube:9000 \
                      -Dsonar.login=admin \
                      -Dsonar.password=admin
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh '''
                docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
