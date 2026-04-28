pipeline {
    agent any

    stages {

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m venv venv || python -m venv venv
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
                python -m backend.app.main || python3 -m backend.app.main
                '''
            }
        }
    }
}
