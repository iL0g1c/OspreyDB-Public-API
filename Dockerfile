# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src/

# Expose port 5011, which your Flask app uses
EXPOSE 5011

# Set environment variables to prevent Python from writing .pyc files 
# and to ensure stdout and stderr are printed directly to the terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the API script when the container launches
CMD ["python", "src/main-api.py"]