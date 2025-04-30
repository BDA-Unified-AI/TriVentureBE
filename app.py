from dotenv import load_dotenv
import base64
import json
import os

load_dotenv(override=True)
encoded_env = os.getenv("ENCODED_ENV")
if encoded_env:
    # Decode the base64 string
    decoded_env = base64.b64decode(encoded_env).decode()

    # Load it as a dictionary
    env_data = json.loads(decoded_env)

    # Set environment variables
    for key, value in env_data.items():
        os.environ[key] = value
from src.apis.create_app import create_app, api_router
import uvicorn


app = create_app()

app.include_router(api_router)
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3002)
