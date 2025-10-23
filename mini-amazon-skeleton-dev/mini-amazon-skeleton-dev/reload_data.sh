#!/bin/bash

# Script to reload mock data into the database
# Make sure to update the connection details below

DB_HOST="localhost"
DB_NAME="mini_amazon"
DB_USER="postgres"

echo "Reloading mock data into database..."

# Drop and recreate tables
echo "Recreating database schema..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f db/create.sql

# Load data from CSV files
echo "Loading data from CSV files..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f db/load.sql

echo "Data reload complete! Refresh your browser to see the new products."
