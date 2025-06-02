#!/bin/bash

set -e

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