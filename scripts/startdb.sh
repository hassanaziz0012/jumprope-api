#!/bin/bash

# Create a local directory for Postgres data if it doesn't exist
mkdir -p ./postgres_data

# Run the Postgres Docker container with a volume mapped to the local directory
docker run --name temp-postgres \
  -e POSTGRES_PASSWORD=temppassword \
  -v $(pwd)/postgres_data:/var/lib/postgresql \
  -e PGDATA=/var/lib/postgresql/data \
  -p 5432:5432 \
  -d postgres
