#!/bin/bash

# Define variables
IMAGE_NAME="ospreydb-api"
CONTAINER_NAME="ospreydb-api-instance"
PORT="5011"

echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

# Check if a container with the same name is already running and remove it
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

echo "Starting container with $STORAGE_LIMIT limit..."
# Runs the API using the specified port and environment variables
# Applies the hard storage limit and log rotation
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:$PORT \
  --env-file src/.env \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  $IMAGE_NAME

echo "Deployment complete."
echo "API is running on http://localhost:$PORT"