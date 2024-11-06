#!/bin/bash
set -e

# Wait for services if enabled
if [ "$WAIT_FOR_DB" = "true" ]; then
    echo "Waiting for database..."
    dockerize -wait tcp://${DB_HOST}:${DB_PORT} -timeout 60s
fi

if [ "$WAIT_FOR_REDIS" = "true" ]; then
    echo "Waiting for Redis..."
    dockerize -wait tcp://${REDIS_HOST}:${REDIS_PORT} -timeout 60s
fi

if [ "$WAIT_FOR_QDRANT" = "true" ]; then
    echo "Waiting for Qdrant..."
    dockerize -wait tcp://${QDRANT_HOST}:${QDRANT_PORT} -timeout 60s
fi

# Execute the passed command
exec "$@"