# Use the official Python image from Docker Hub
FROM python:3.12-slim

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y libgomp1 gcc g++ && \
    rm -rf /var/lib/apt/lists/*

    

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary project folders and app.py into the container
COPY app.py ./
COPY data ./data
COPY Model_Files ./Model_Files
COPY routes ./routes
COPY services ./services
COPY static ./static
COPY templates ./templates

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["flask", "run"]
