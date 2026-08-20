@Library('my-shared-lib') _

pipeline {
    agent any

    environment {
        IMAGE_NAME = "cv-ranker-lab"
        IMAGE_VERSION = "v1.1.0"
        REGISTRY = "localhost:5000"
    }

    stages {
        stage('Setup Environment') {
            steps {
                script {
                    // Lấy short SHA an toàn để tránh lỗi NullPointer ở global environment
                    def shortCommit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${shortCommit}-${env.BUILD_NUMBER}"
                }
            }
        }

        stage('Build and Scan') {
            steps {
                buildAndScanImage("${IMAGE_NAME}", "${env.IMAGE_TAG}", "Dockerfile.multistage")
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                }
            }
            steps {
                dir('app') {
                    sh 'pip install --no-cache-dir -r requirements.txt'
                    sh 'pytest test_main.py -v'
                }
            }
        }

        stage('Lint') {
            agent {
                docker {
                    image 'python:3.11-slim'
                }
            }
            steps {
                dir('app') {
                    sh 'pip install --no-cache-dir flake8'
                    sh 'flake8 . --max-line-length=100 --exclude=test_main.py'
                }
            }
        }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    docker tag ${IMAGE_NAME}:${env.IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${env.IMAGE_TAG}
                    docker tag ${IMAGE_NAME}:${env.IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}
                    docker tag ${IMAGE_NAME}:${env.IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:production

                    docker push ${REGISTRY}/${IMAGE_NAME}:${env.IMAGE_TAG}
                    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}
                    docker push ${REGISTRY}/${IMAGE_NAME}:production
                """
            }
        }

        stage('Smoke Test') {
            when { branch 'main' }
            steps {
                withCredentials([string(
                    credentialsId: 'db-password',
                    variable: 'DB_PASSWORD'
                )]) {
                    sh """
                        echo "DB_PASSWORD=\$DB_PASSWORD" > .env
                        export API_IMAGE=${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}
                        docker compose -f docker-compose.yml up -d
                    """
                    sleep 10
                    sh """
                        curl -f http://localhost:8000/health
                        curl -f http://localhost:8000/db-check
                        curl -f http://localhost:8000/cache-check
                    """
                }
            }
            post {
                always {
                    // Đảm bảo dọn dẹp container kể cả khi curl bị lỗi (HTTP 500/timeout)
                    sh 'docker compose down -v || true'
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE_NAME}:${env.IMAGE_TAG} || true"
        }
        failure {
            echo 'Pipeline thất bại - kiểm tra log ở Stage bị đỏ.'
        }
    }
}