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
                docker { image 'python:3.11-slim' }
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
                docker { image 'python:3.11-slim' }
            }
            steps {
                dir('app') {
                    sh 'pip install --no-cache-dir flake8'
                    sh 'flake8 . --max-line-length=100 --exclude=test_main.py'
                }
            }
        }

        // ĐƯA SMOKE TEST LÊN TRƯỚC PUSH
        stage('Smoke Test') {
            steps {
                withCredentials([string(credentialsId: 'db-password', variable: 'DB_PASSWORD')]) {
                    withEnv([
                        "DB_PASSWORD=${DB_PASSWORD}",
                        "API_IMAGE=${IMAGE_NAME}:${env.IMAGE_TAG}"
                    ]) {
                        sh 'docker compose -f docker-compose.yml up -d'
                        
                        // Chờ PostgreSQL healthcheck hoàn tất thay vì sleep cố định
                        sh 'sleep 15' 
                        
                        sh '''
                            curl -f http://localhost:8000/health
                            curl -f http://localhost:8000/db-check
                            curl -f http://localhost:8000/cache-check
                        '''
                    }
                }
            }
            post {
                always {
                    sh 'docker compose down -v || true'
                }
            }
        }

        stage('Push') {
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