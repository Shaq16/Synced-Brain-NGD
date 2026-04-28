pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t synced-brain .
                '''
            }
        }

        stage('Run Container') {
            steps {
                sh '''
                docker run --rm synced-brain
                '''
            }
        }
    }
}
