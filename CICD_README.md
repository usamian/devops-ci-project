# DevOps CI/CD Pipeline Assignment

This repository contains a complete CI/CD pipeline setup using Jenkins, SonarQube, and Docker.

## Assignment Requirements Covered

1. **GitHub Repository**: `devops-ci-project`
2. **Sample Project**: Python-based Atlas-AI application
3. **Branching**: `ci-cd-pipeline` branch created
4. **Docker Installation**: `docker-install.sh` script included
5. **Docker Compose**: Complete Jenkins and SonarQube setup
6. **Jenkins Pipeline**: Declarative pipeline for code checkout, SonarQube analysis, and Docker build
7. **File Submission**: All required files added to GitHub

## Components

### 1. Docker Installation Script (`docker-install.sh`)
- Automated Docker and Docker Compose installation for Ubuntu/Debian
- Includes GPG key setup and repository configuration
- Removes old Docker versions to avoid conflicts
- Adds current user to docker group for sudo-less operation

### 2. Docker Compose File (`docker-compose.yml`)
Sets up the following services:

#### Jenkins
- Image: `jenkins/jenkins:lts`
- Ports: 8080 (web), 50000 (agent)
- Runs as root user with Docker socket mount for building images
- Auto-executes setup wizard disabled

#### SonarQube
- Image: `sonarqube:community`
- Port: 9000
- Requires PostgreSQL database
- Data persisted through volumes

#### PostgreSQL
- Image: `postgres:15`
- Database: `sonarqube`
- User/Password: `sonar/sonar`

### 3. Jenkins Pipeline (`Jenkinsfile`)

The declarative pipeline performs the following stages:

```text
Checkout Code --> SonarQube Analysis --> Build Docker Image
```

#### Stages:
1. **Checkout Code**: Pulls latest code from the repository
2. **SonarQube Analysis**: Runs code quality and security analysis
   - Project Key: `atlas-ai`
   - Sources: `src/` directory
   - Encoding: UTF-8
3. **Build Docker Image**: Builds the application Docker image

### 4. Sample Application
- Language: Python 3.11
- Framework: Flask-based web API
- Includes NLP and rule-based components
- Exposed on port 5000

## Setup Instructions

### Step 1: Install Docker
```bash
chmod +x docker-install.sh
./docker-install.sh
```

Log out and back in for group changes to take effect.

### Step 2: Start Services
```bash
docker-compose up -d
```

### Step 3: Access Services
- **Jenkins**: http://localhost:8080
- **SonarQube**: http://localhost:9000
  - Default credentials: admin/admin (change on first login)

### Step 4: Configure Jenkins
1. Navigate to http://localhost:8080
2. Complete initial admin setup
3. Go to **Manage Jenkins** > **Credentials**
4. Add a new **Secret text** credential:
   - Kind: Secret text
   - Secret: Your SonarQube token (generate from SonarQube user profile)
   - ID: `sonarqube-token`

### Step 5: Configure SonarQube in Jenkins
1. Go to **Manage Jenkins** > **System**
2. Scroll to **SonarQube servers**
3. Add SonarQube server:
   - Name: `sonarqube-server`
   - URL: `http://sonarqube:9000`
   - Server authentication token: `sonarqube-token`

### Step 6: Run Pipeline
The pipeline will automatically trigger when you push code to the repository configured in Jenkins.

## File Structure
```
.
├── docker-install.sh          # Docker installation script
├── docker-compose.yml         # Jenkins + SonarQube + PostgreSQL setup
├── Jenkinsfile                # CI/CD declarative pipeline
├── Dockerfile                 # Application container definition
├── requirements.txt           # Python dependencies
├── src/                       # Source code
├── data/                      # Knowledge base data
└── README.md                  # This file
```

## Credentials Reference

### SonarQube
- **URL**: http://localhost:9000
- **Username**: admin
- **Password**: Usama7862601...
  (ends with three dots as specified)

### PostgreSQL
- **User**: sonar
- **Password**: sonar
- **Database**: sonarqube

### Jenkins
- URL: http://localhost:8080
- Initial admin password: Check `docker logs jenkins-server`

## Notes

- Jenkins container has Docker socket mounted (`/var/run/docker.sock`) to enable Docker commands from within the container
- All data is persisted through Docker volumes
- SonarQube runs with authentication disabled for initial setup

---
*Assignment completed for DevOps course*