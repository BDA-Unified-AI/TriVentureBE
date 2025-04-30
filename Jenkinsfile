pipeline {
    agent any
    
    environment {
        APP_PORT = '7860'
        GITHUB_CREDENTIALS_ID = 'github-credentials'
        ENV_FILE_ID = 'env-file-secret'
        VENV_NAME = 'venv'
        PYTHON_VERSION = 'python3'
        MAX_RETRIES = '10'  // Maximum number of retries for health check
        RETRY_INTERVAL = '2'  // Seconds between retries
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/BDA-Unified-AI/TriVenture-BE',
                        credentialsId: "${GITHUB_CREDENTIALS_ID}"
                    ]]
                ])
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    try {
                        // Kill any existing uvicorn processes
                        sh 'pkill -f uvicorn || true'
                        
                        // Create and activate virtual environment
                        sh """
                            ${PYTHON_VERSION} -m venv ${VENV_NAME}
                            . ${VENV_NAME}/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        """
                    } catch (Exception e) {
                        error "Failed to setup Python environment: ${e.message}"
                    }
                }
            }
        }
        
        stage('Run Application') {
            steps {
                script {
                    try {
                        withCredentials([file(credentialsId: "${ENV_FILE_ID}", variable: 'ENV_FILE')]) {
                            sh """#!/bin/bash
                                # Load environment variables using grep and export
                                grep -v '^#' "\${ENV_FILE}" | while IFS='= ' read -r key value; do
                                    if [ ! -z "\$key" ]; then
                                        export "\$key=\$value"
                                    fi
                                done
                                
                                # Start the FastAPI application
                                . ${VENV_NAME}/bin/activate
                                
                                # Start uvicorn with log file
                                nohup uvicorn app.main:app \
                                    --host 0.0.0.0 \
                                    --port ${APP_PORT} \
                                    --workers 2 \
                                    > app.log 2>&1 &
                                
                                # Store the PID
                                echo \$! > app.pid
                                
                                # Wait and verify the application is running
                                attempts=0
                                while [ \$attempts -lt ${MAX_RETRIES} ]; do
                                    sleep ${RETRY_INTERVAL}
                                    if curl -s http://localhost:${APP_PORT}/docs > /dev/null; then
                                        echo "Application started successfully"
                                        exit 0
                                    fi
                                    attempts=\$((attempts + 1))
                                    echo "Attempt \$attempts/${MAX_RETRIES}: Waiting for application to start..."
                                    
                                    # Check if process is still running
                                    if ! ps -p \$(cat app.pid) > /dev/null; then
                                        echo "ERROR: Application process died. Last logs:"
                                        tail -n 50 app.log
                                        exit 1
                                    fi
                                done
                                
                                echo "ERROR: Application failed to start within timeout. Last logs:"
                                tail -n 50 app.log
                                exit 1
                            """
                        }
                    } catch (Exception e) {
                        error "Failed to start application: ${e.message}"
                    }
                }
            }
        }
    }
    
    post {
        failure {
            // Cleanup on failure
            sh '''
                if [ -f app.pid ]; then
                    kill $(cat app.pid) || true
                    rm app.pid
                fi
                pkill -f uvicorn || true
                rm -rf ${VENV_NAME}
            '''
        }
        success {
            archiveArtifacts artifacts: 'app.log,app.pid', allowEmptyArchive: true
        }
    }
}