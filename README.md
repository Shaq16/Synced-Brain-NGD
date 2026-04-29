---

## 🚀 DevOps Setup — Jenkins + Docker (CI/CD Pipeline)

This project implements a **Continuous Integration and Continuous Deployment (CI/CD)** pipeline using Jenkins and Docker.

---

### 🔁 CI/CD Workflow

```
GitHub (Code Push)
    ↓
Jenkins Pipeline Trigger
    ↓
Build Docker Image (CI)
    ↓
Run / Test Backend (CI)
    ↓
Deploy Container (CD)
    ↓
Application running on localhost:8000
```

---

### ⚙️ Tools Used

| Tool | Purpose |
|------|---------|
| Jenkins | CI/CD automation |
| Docker | Containerization & deployment |
| GitHub | Source code management |
| FastAPI | Backend service |

---

### 🐳 Docker Setup

The application is containerized using Docker.

**Build Image**
```bash
docker build -t synced-brain .
```

**Run Container**
```bash
docker run -d -p 8000:8000 --name synced-brain-container synced-brain
```

---

### ⚡ Jenkins Setup

Jenkins is run using Docker:

```bash
docker run -d -p 9090:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name jenkins jenkins/jenkins:lts
```

Access Jenkins at: `http://localhost:9090`

---

### 🧪 CI/CD Pipeline (Jenkinsfile)

The pipeline automates build, test, and deployment:

```groovy
pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t synced-brain .'
            }
        }

        stage('Test / Run Backend') {
            steps {
                sh 'docker run --rm synced-brain'
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
```

---

### 🔄 Continuous Integration (CI)

- ✅ Automatically builds Docker image
- ✅ Runs backend to verify functionality
- ✅ Detects errors (e.g., missing dependencies)

> **Trigger:** Manual (`Build Now`) or GitHub push (if webhook configured)

---

### 🚀 Continuous Deployment (CD)

- ✅ Automatically stops old container
- ✅ Deploys new container with latest code
- ✅ Application is immediately available after pipeline completes

> No manual deployment required.

---

### ⚡ Optimization

- Docker layer caching is used
- Dependencies install only when `requirements.txt` changes
- Faster builds compared to traditional CI setups

---

### 🧪 Validation Steps

1. Modify backend code (e.g., update an API response)
2. Push changes to GitHub
3. Trigger the Jenkins pipeline
4. Verify:
   - Build success in Jenkins console logs
   - Container restarted (`docker ps`)
   - Updated output visible at `http://localhost:8000`

---

### 📸 Demo Evidence

- Jenkins Console Output (build, test, deploy stages)
- Running container (`docker ps`)
- Application response from browser

---

### ⚠️ Notes

- Webhooks are not configured due to localhost limitations
- Pipeline is triggered manually in Jenkins
- Deployment is local (suitable for academic demonstration)