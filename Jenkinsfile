pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "atlas-ai-app"
        IMAGE_TAG = "latest"
        SONAR_HOST_URL = "http://sonarqube:9000"
        SONAR_TOKEN = credentials('sonarqube-token')
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
                          -Dsonar.login=$SONAR_TOKEN \
                          -Dsonar.sourceEncoding=UTF-8
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
