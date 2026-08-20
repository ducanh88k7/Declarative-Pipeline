pipeline {
    agent any
    
    environment {
        IMAGE_NAME = 'cv-ranker-lab'
        IMAGE_TAG = "cv-ranker-lab:${GIT_COMMIT.take(7)}-${BUILD_NUMBER}"
    }

    stages {
        stage('Setup Environment') {
            steps {
                script {
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build and Scan') {
            steps {
                sh "docker build -f Dockerfile.multistage -t ${IMAGE_TAG} --provenance=false --sbom=false ."
                sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${IMAGE_TAG}"
            }
        }

        stage('Test') {
            agent {
                docker { 
                    image 'python:3.11-slim'
                    reuseNode true 
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
                    reuseNode true 
                }
            }
            steps {
                dir('app') {
                    sh 'pip install --no-cache-dir flake8'
                    sh 'flake8 . --max-line-length=100 --exclude=test_main.py'
                }
            }
        }

        stage('Smoke Test') {
            steps {
                withCredentials([string(credentialsId: 'db-password', variable: 'DB_PASSWORD')]) {
                    sh '''
                        IMAGE_TAG=${IMAGE_TAG} docker compose -f docker-compose.yml up -d
                        
                        # Chờ PostgreSQL & Redis healthy
                        sleep 10
                        
                        API_CONTAINER=$(docker compose ps -q api)
                        API_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $API_CONTAINER)
                        
                        # Thêm retry cho curl để tránh bẫy race condition
                        curl --connect-timeout 5 --retry 5 --retry-delay 3 --retry-connrefused http://$API_IP:8000/health
                    '''
                }
            }
            post {
                failure {
                    // Bắt log ngay nếu smoke test xịt trước khi down container
                    sh 'docker compose logs api'
                }
                always {
                    sh 'docker compose down -v'
                }
            }
        }

        stage('Push') {
            steps {
                echo "Thêm lệnh Docker Push của bạn tại đây"
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE_TAG} || true"
        }
        failure {
            echo 'Pipeline thất bại - kiểm tra log ở Stage bị đỏ.'
        }
    }
}