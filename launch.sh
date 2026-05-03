#!/bin/bash
# Script to launch the ContestKeeper project locally

# Get the directory where the script is located
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Change to the application directory
cd ContestKeeper || exit 1

# Start the Django development server
echo "Starting server on http://127.0.0.1:8000/..."
python3 manage.py runserver
