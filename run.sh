#!/bin/bash

# Define the image name
IMAGE_NAME="nbsanity"

# Build the Docker image
docker build -t $IMAGE_NAME .

# Run the Docker container locally with a specified port for testing
TEST_PORT=8000
docker run -e PORT=$TEST_PORT -p $TEST_PORT:$TEST_PORT $IMAGE_NAME
