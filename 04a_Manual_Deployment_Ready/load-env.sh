#!/bin/bash
#
# This script loads environment variables from a .env file in the same directory.
#
# Usage:
#   source load-env.sh

if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(cat .env | grep -v '#' | sed 's/\n/\\n/g' | xargs)
  echo "Environment variables loaded."
else
  echo "Error: .env file not found."
  echo "Please create a .env file with the required environment variables."
  echo "You can use .env.example as a template."
  exit 1
fi
