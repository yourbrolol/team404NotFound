#!/bin/bash

# Define filenames
DB_FILE="db.sqlite3"
TEST_DB_FILE="test_db.sqlite3"

# Change directory to the script's location (optional but good practice)
cd "$(dirname "$0")"

# Delete db.sqlite3 if it exists
if [ -f "$DB_FILE" ]; then
    echo "Deleting existing $DB_FILE..."
    rm "$DB_FILE"
fi

# Copy test_db.sqlite3 to db.sqlite3
if [ -f "$TEST_DB_FILE" ]; then
    echo "Copying $TEST_DB_FILE to $DB_FILE..."
    cp "$TEST_DB_FILE" "$DB_FILE"
    echo "Success!"
else
    echo "Error: $TEST_DB_FILE not found!"
    exit 1
fi
