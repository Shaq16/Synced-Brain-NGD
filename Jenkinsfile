pipeline {
    agent any

    stages {

        stage('Install Dependencies') {
            steps {
                bat 'python -m venv venv'
                bat 'venv\\Scripts\\activate && pip install -r backend/requirements.txt'
            }
        }

        stage('Run Backend') {
            steps {
                bat 'venv\\Scripts\\activate && python -m backend.app.main'
            }
        }
    }
}
