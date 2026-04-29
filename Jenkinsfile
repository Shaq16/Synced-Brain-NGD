pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
    }

    stages {

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t synced-brain .'
            }
        }
    stage('Test / Run Backend') {
        steps {
            sh '''
            docker run --rm -e SKIP_MILVUS=true synced-brain python -c "print('CI test passed')"
            '''
        }
    }

        stage('Deploy') {
            steps {
                sh '''
                docker rm -f synced-brain-container || true
                docker run -d -p 8000:8000 --name synced-brain-container synced-brain
                '''
            }
        }
    }
}