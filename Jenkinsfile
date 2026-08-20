pipeline {
    agent any
    
    environment {
        // Tên image dựa theo project CV Ranker AI của bạn
        IMAGE_NAME = 'cv-ranker-lab'
    }

    stages {
        stage('Setup Environment') {
            steps {
                script {
                    // Lấy mã hash ngắn của commit
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build and Scan') {
            steps {
                // Build Multistage Dockerfile và scan với Trivy
                sh "docker build -f Dockerfile.multistage -t ${IMAGE_NAME}:${SHORT_COMMIT}-${BUILD_NUMBER} --provenance=false --sbom=false ."
                sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${IMAGE_NAME}:${SHORT_COMMIT}-${BUILD_NUMBER}"
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
                // Thay thế 'YOUR_CREDENTIAL_ID' bằng ID credential chứa mật khẩu DB trên Jenkins của bạn
                withCredentials([string(credentialsId: 'db-password', variable: 'DB_PASSWORD')]) {
                    // Sử dụng dấu nháy đơn (''') để script được thực thi dưới dạng shell thuần túy, tránh lỗi nội suy Groovy
                    sh '''
                        # Khởi động cụm dịch vụ
                        docker compose -f docker-compose.yml up -d
                        
                        # Chờ PostgreSQL (pgvector) và API khởi động hoàn tất
                        sleep 15
                        
                        # Lấy Container ID của service API (giả sử tên service trong docker-compose.yml là 'api')
                        API_CONTAINER=$(docker compose ps -q api)
                        
                        # Trích xuất IP động của container API trên Docker bridge network
                        API_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $API_CONTAINER)
                        
                        # Curl thẳng vào IP của API container thay vì localhost
                        curl -f http://$API_IP:8000/health
                    '''
                }
            }
            post {
                always {
                    // Xóa resource để dọn dẹp workspace sau khi test
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
            // Xóa Docker image cũ để giải phóng bộ nhớ
            sh "docker rmi ${IMAGE_NAME}:${SHORT_COMMIT}-${BUILD_NUMBER} || true"
        }
        failure {
            echo 'Pipeline thất bại - kiểm tra log ở Stage bị đỏ.'
        }
    }
}