#!/usr/bin/env python3
"""
Simple script to check if profile updates are saved in the database
"""
import os
import sys
sys.path.append('.')

# Set up environment variables (adjust these to match your setup)
os.environ['DB_NAME'] = 'amazon'
os.environ['DB_USER'] = 'ubuntu'
os.environ['DB_PORT'] = '5432'
os.environ['DB_HOST'] = 'postgres'
os.environ['DB_PASSWORD'] = 'your_password'
os.environ['SECRET_KEY'] = 'test_secret_key'

from app import create_app
from app.models.user import User

def check_user_profile(user_id=1):
    """Check a user's profile in the database"""
    app = create_app()
    
    with app.app_context():
        try:
            user = User.get(user_id)
            if user:
                print(f"=== User Profile (ID: {user_id}) ===")
                print(f"Name: {user.firstname} {user.lastname}")
                print(f"Email: {user.email}")
                print(f"Address: {user.address}")
                print(f"Balance: ${user.balance}")
                print("=" * 30)
                return True
            else:
                print(f"No user found with ID {user_id}")
                return False
        except Exception as e:
            print(f"Error checking user profile: {e}")
            return False

if __name__ == "__main__":
    print("Checking user profile in database...")
    check_user_profile()
