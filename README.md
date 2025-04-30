# TriVenture Backend Application (Public Version)

This repository contains the backend API for TriVenture, built with FastAPI, MongoDB, and LangChain/LangGraph for AI capabilities.

## 2. Installation Guides

### 2.1 System Requirements

Before installing and running the TriVenture backend application, ensure your system meets the following requirements:

#### Operating System
- **Windows:** Windows 10 or later
- **macOS:** macOS 10.15 (Catalina) or later
- **Linux:** Ubuntu 18.04+, Debian 10+, or other modern Linux distributions

#### Required Software
- **Python:** Version 3.10 or later
- **pip:** Latest version
- **Docker & Docker Compose:** Latest version (optional, for containerized deployment)
- **Git:** Latest version recommended

#### Required Libraries/Frameworks
- FastAPI
- Uvicorn (ASGI server)
- LangChain & LangGraph
- MongoDB driver (motor)
- Firebase Admin SDK
- See requirements.txt for the complete list

#### Database Requirements
- **MongoDB:** Version 5.0 or later
- Connection string and credentials

#### API Keys/Credentials Needed
- AI model API keys (Google Gemini or other)
- MongoDB connection string
- Firebase service account credentials
- JWT secret key

### 2.2 Installation Instructions

Follow these steps to set up and run the TriVenture backend application on your local machine:

#### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd TriVenture/BE
```

#### Step 2: Set Up a Python Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
Create a `.env` file in the root directory of the project with the following variables (replace with your actual values):

```
# MongoDB Configuration
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/<database-name>
MONGODB_DB_NAME=your_database_name

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/LLM Configuration
GOOGLE_API_KEY=your_google_api_key

# Firebase Configuration
FIREBASE_CREDENTIAL_PATH=path/to/firebase-credentials.json

# Server Configuration
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

#### Step 5: Set Up MongoDB
- Ensure MongoDB is running and accessible via the connection string provided in your `.env` file
- The application will automatically create collections as needed

#### Step 6: Start the Application
```bash
# Development mode with auto-reload
uvicorn app:app --host 0.0.0.0 --port 3002 --reload
```

The API will be available at http://localhost:3002 with Swagger documentation at http://localhost:3002

#### Step 7: Alternative - Docker Deployment
If you prefer to use Docker:

```bash
# Build and start the container
docker-compose up -d --build
```

This will start the application at http://localhost:7860

## Troubleshooting

- **Database Connection Issues**: Ensure MongoDB is running and your connection string is correct
- **Missing Dependencies**: If you encounter errors about missing packages, try reinstalling requirements with `pip install -r requirements.txt`
- **Environment Variables**: Make sure all required environment variables are properly set in your `.env` file
- **Port Conflicts**: If the port is already in use, specify a different port using `--port` when starting Uvicorn

## API Documentation

Once the application is running, API documentation is available at:
- Swagger UI: http://localhost:3002
- OpenAPI JSON: http://localhost:3002/openapi.json

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
