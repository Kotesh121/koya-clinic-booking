
pipeline {
    agent any

    environment {
        APP_DIR = '/opt/koya-clinic/koya-clinic-booking'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Docker') {
            steps {
                sh '''
                    docker --version
                    docker compose version
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    cd ${APP_DIR}
                    docker compose build
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    cd ${APP_DIR}
                    docker compose up -d
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    cd ${APP_DIR}
                    docker compose ps
                    docker compose logs --tail=50
                '''
            }
        }
    }

    post {
        success {
            echo 'Koya Clinic Booking deployment successful!'
        }

        failure {
            echo 'Deployment failed. Check Jenkins console logs.'
        }
    }
}

