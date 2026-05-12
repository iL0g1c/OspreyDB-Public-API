# Use a specific, slim version for a smaller attack surface
FROM python:3.11-slim

# Create a non-privileged user to run the application
RUN useradd -m -s /bin/bash appuser

# Set the working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# Change ownership of the app directory to our non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-privileged user
USER appuser

# Expose the application port
EXPOSE 5011

# Standard Python environment hygiene
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the API script
CMD ["python", "src/main-api.py"]