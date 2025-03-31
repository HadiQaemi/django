#!/bin/bash

set -e

# Function to check if MongoDB is ready
function wait_for_mongodb() {
  echo "Waiting for MongoDB to start..."
  while ! nc -z $MONGO_HOST $MONGO_PORT; do
    sleep 1
  done
  echo "MongoDB started"
}

# Function to check if Redis is ready
function wait_for_redis() {
  echo "Waiting for Redis to start..."
  while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 1
  done
  echo "Redis started"
}

# Function to check if Elasticsearch is ready
function wait_for_elasticsearch() {
  echo "Waiting for Elasticsearch to start..."
  while ! nc -z $ELASTIC_HOST $ELASTIC_PORT; do
    sleep 1
  done
  echo "Elasticsearch started"
}

# Wait for services to be ready
wait_for_mongodb
wait_for_redis
wait_for_elasticsearch

# Check if we need to apply migrations
if [ "$APPLY_MIGRATIONS" = "true" ]; then
  echo "Applying database migrations..."
  python manage.py migrate
fi

# Create data directories if they don't exist
mkdir -p /app/data/

# Check if we need to load initial data
if [ "$LOAD_INITIAL_DATA" = "true" ]; then
  echo "Loading initial data..."
  python manage.py migrate_data --source=file --input=/app/data/initial_urls.json
fi

# Execute the command
exec "$@"