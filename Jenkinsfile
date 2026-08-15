pipeline {
    agent any

    environment {
        IMAGE_NAME = "cv-ranker-lab"
        IMAGE_TAG = "${env.GIT_COMMIT[0..7]}"
    }

    stages {
        stage('Build') {
            steps {
                sh "docker build -f Dockerfile.multistage -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                }
            }
            steps {
                sh 'cd app && pip install --no-cache-dir -r requirements.txt'
                sh 'cd app && pytest test_main.py -v'
            }
        }

        stage('Lint') {
            agent {
                docker {
                    image 'python:3.11-slim'
                }
            }
            steps {
                sh 'cd app && pip install --no-cache-dir flake8'
                sh 'cd app && flake8 . --max-line-length=100 --exclude=test_main.py'
            }
        }

        stage('Scan') {
            steps {
                sh "trivy image --severity HIGH,CRITICAL --exit-code 1 ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'registry-credentials',
                    usernameVariable: 'REG_USER',
                    passwordVariable: 'REG_PASS'
                )]) {
                    sh 'echo $REG_PASS | docker login -u $REG_USER --password-stdin myregistry.example.com'
                    sh "docker push myregistry.example.com/${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
        }
        failure {
            echo 'Pipeline thất bại - kiểm tra log ở Stage bị đỏ.'
        }
    }
}