pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "atlas-ai-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONAR_HOST_URL = "http://sonarqube:9000"
        SONAR_TOKEN = "squ_4e8fc8fdbd46457acc13275a8cfcfed5eeda229a"
        PATH = "${env.PATH}:/var/jenkins_home/bin"
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
                      -Dsonar.token=squ_4e8fc8fdbd46457acc13275a8cfcfed5eeda229a \
                      -Dsonar.sourceEncoding=UTF-8
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo "Docker build step - skipping for now"
                echo "Docker CLI not available in Jenkins container"
                echo "Pipeline will succeed after SonarQube analysis"
            }
        }
    }
    
    post {
        success {
            echo "Pipeline completed successfully!"
            echo "SonarQube analysis: http://localhost:9000/dashboard?id=atlas-ai"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
