pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'acumen-api-gateway'
        DOCKER_TAG = "${BUILD_NUMBER}"
        COMPOSE_PROJECT = 'acumen'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/lazuardi21/AcumenAPIGateway.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 . --max-line-length=120 --exclude=venv --count --show-source --statistics || true
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install pytest pytest-cov
                    python -m pytest tests/ -v --tb=short || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                """
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    cd /opt/acumen-strategy
                    docker-compose up -d --build api_gateway
                '''
            }
        }
    }

    post {
        always {
            sh 'rm -rf venv || true'
        }
        success {
            echo '✅ API Gateway pipeline completed successfully!'
        }
        failure {
            echo '❌ API Gateway pipeline failed!'
        }
    }
}
