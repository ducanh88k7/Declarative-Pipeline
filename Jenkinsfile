@Library('my-shared-lib') _

pipeline {
    agent any

    environment {
        IMAGE_NAME = "cv-ranker-lab"
        IMAGE_TAG = "${env.GIT_COMMIT[0..7]}-${env.BUILD_NUMBER}"
        IMAGE_VERSION = "v1.1.0"
        REGISTRY = "localhost:5000"
    }

    stages {
        // stage('Build') {
        //     steps {
        //         sh "docker build -f Dockerfile.multistage -t ${IMAGE_NAME}:${IMAGE_TAG} --provenance=false --sbom=false ."
        //     }
        // }

        stage('Build and Scan') {
            steps {
                buildAndScanImage("${IMAGE_NAME}", "${IMAGE_TAG}", "Dockerfile.multistage")
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

        // stage('Scan') {
        //     steps {
        //         // TODO: msgpack/setuptools báo vulnerable qua Trivy chạy trong Jenkins (DooD)
        //         // dù xác nhận độc lập filesystem image đã sạch (xem ghi chú ngày hôm nay).
        //         // Tạm hạ --exit-code để không chặn Pipeline, cần điều tra thêm sau.
        //         sh "trivy image --severity HIGH,CRITICAL --exit-code 0 ${IMAGE_NAME}:${IMAGE_TAG}" đúng 
        //     }
        // }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:production

                    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
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
                        sleep 5
                        curl -f http://localhost:8000/health
                        curl -f http://localhost:8000/db-check
                        curl -f http://localhost:8000/cache-check
                        docker compose down -v
                    """
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