# Use the slim variant of Python 3.11 to reduce the size
FROM python:3.11-slim

# Add a non-root user for better security
RUN useradd -m -u 1000 user

# Switch to non-root user
USER user

# Ensure pip, setuptools, and wheel are up to date
RUN python -m pip install --upgrade pip setuptools wheel

# Set PATH to include user installs
ENV PATH="/home/user/.local/bin:$PATH"

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt file and install dependencies
COPY --chown=user ./requirements.txt /app/requirements.txt

# Install only necessary dependencies from the requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code to the working directory
COPY --chown=user . /app

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
