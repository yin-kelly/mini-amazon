# Migration script to create new tables
# Run this with: python migrate.py

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import DB

def run_migration():
    app = create_app()
    with app.app_context():
        db = DB(app)
        
        # Read the SQL file
        with open('db/add_new_features.sql', 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for stmt in statements:
            if stmt and not stmt.startswith('--'):
                try:
                    db.execute(stmt)
                    print(f'✓ Executed: {stmt[:60]}...')
                except Exception as e:
                    print(f'✗ Error: {stmt[:60]}... - {e}')
        
        print('Migration completed!')

if __name__ == '__main__':
    run_migration()
