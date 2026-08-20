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

                        echo "Waiting for PostgreSQL..."
                        sleep 10

                        docker compose ps

                        echo "Testing API /health..."

                        docker compose exec -T api \
                            python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health', timeout=5).read().decode())"
                    '''
                }
            }

            post {
                failure {
                    sh 'docker compose logs api || true'
                }
                always {
                    sh 'docker compose down -v'
                }
            }
        }

        stage('Push') {
            steps {
                sh '''
                    docker tag ${IMAGE_TAG} local-registry:5000/cv-ranker-lab:v1.2.0
                    docker push local-registry:5000/cv-ranker-lab:v1.2.0
                '''
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE_NAME}:${SHORT_COMMIT}-${BUILD_NUMBER} || true"
        }
        failure {
            echo 'Pipeline thất bại - kiểm tra log ở Stage bị đỏ.'
        }
    }
}