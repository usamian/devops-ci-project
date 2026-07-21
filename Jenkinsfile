pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "atlas-ai-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONAR_HOST_URL = "http://sonarqube:9000"
        SONAR_LOGIN = "admin"
        SONAR_PASSWORD = "Usama7862601"
        PATH = "${env.PATH}:/tmp/bin"
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
                sh '''
                    sonar-scanner \
                      -Dsonar.projectKey=atlas-ai \
                      -Dsonar.sources=src/ \
                      -Dsonar.host.url=http://sonarqube:9000 \
                      -Dsonar.login=admin \
                      -Dsonar.password=Usama7862601 \
                      -Dsonar.sourceEncoding=UTF-8
                '''
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
