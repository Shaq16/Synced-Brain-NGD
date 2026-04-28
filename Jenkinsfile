pipeline {
    agent any

    stages {

        stage('Install Python') {
            steps {
                sh '''
                apt-get update
                apt-get install -y python3 python3-pip python3-venv
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r backend/requirements.txt
                '''
            }
        }

        stage('Run Backend') {
            steps {
                sh '''
                . venv/bin/activate
                python -m backend.app.main
                '''
            }
        }
    }
}
