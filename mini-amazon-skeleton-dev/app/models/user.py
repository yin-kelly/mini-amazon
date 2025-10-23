from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .. import login  # your LoginManager

class User(UserMixin):
    def __init__(self, id, email, firstname, lastname, balance, address=None):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.balance = balance  # <-- needed for profile.html
        self.address = address

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
            SELECT password, id, email, firstname, lastname, balance, address
            FROM Users
            WHERE email = :email
        """, email=email)

        if not rows:  # email not found
            return None
        # rows[0] = (password_hash, id, email, firstname, lastname, balance, address)
        if not check_password_hash(rows[0][0], password):
            return None
        return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
            SELECT email
            FROM Users
            WHERE email = :email
        """, email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname):
        try:
            rows = app.db.execute("""
                INSERT INTO Users(email, password, firstname, lastname)
                VALUES(:email, :password, :firstname, :lastname)
                RETURNING id
            """,
            email=email,
            password=generate_password_hash(password),
            firstname=firstname, lastname=lastname)
            new_id = rows[0][0]
            return User.get(new_id)
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
            SELECT id, email, firstname, lastname, balance, address
            FROM Users
            WHERE id = :id
        """, id=id)
        # rows[0] = (id, email, firstname, lastname, balance, address)
        return User(*(rows[0])) if rows else None

    @staticmethod
    def email_exists_except_user(email, user_id):
        """Check if email exists for any user except the given user_id"""
        rows = app.db.execute("""
            SELECT email
            FROM Users
            WHERE email = :email AND id != :user_id
        """, email=email, user_id=user_id)
        return len(rows) > 0

    @staticmethod
    def update_profile(user_id, firstname, lastname, email, address=None):
        """Update user profile information"""
        try:
            print(f"DEBUG: Updating profile for user {user_id}")
            print(f"DEBUG: New data - firstname: {firstname}, lastname: {lastname}, email: {email}, address: {address}")
            
            result = app.db.execute("""
                UPDATE Users
                SET firstname = :firstname, lastname = :lastname, email = :email, address = :address
                WHERE id = :user_id
            """, firstname=firstname, lastname=lastname, email=email, 
                address=address, user_id=user_id)
            
            print(f"DEBUG: Update result: {result}")
            return True
        except Exception as e:
            print(f"DEBUG: Error updating profile: {str(e)}")
            return False

    @staticmethod
    def update_password(user_id, new_password):
        """Update user password"""
        try:
            app.db.execute("""
                UPDATE Users
                SET password = :password
                WHERE id = :user_id
            """, password=generate_password_hash(new_password), user_id=user_id)
            return True
        except Exception as e:
            print(str(e))
            return False

    @staticmethod
    def verify_password(user_id, password):
        """Verify current password for user"""
        rows = app.db.execute("""
            SELECT password
            FROM Users
            WHERE id = :user_id
        """, user_id=user_id)
        
        if not rows:
            return False
        return check_password_hash(rows[0][0], password)

    @staticmethod
    def update_balance(user_id, amount):
        """Update user balance (positive for top-up, negative for withdrawal)"""
        try:
            # First check current balance
            current_rows = app.db.execute("""
                SELECT balance FROM Users WHERE id = :user_id
            """, user_id=user_id)
            
            if not current_rows:
                return False, "User not found"
            
            current_balance = float(current_rows[0][0])
            new_balance = current_balance + amount
            
            # Check if withdrawal would result in negative balance
            if new_balance < 0:
                return False, "Insufficient funds"
            
            # Update balance
            app.db.execute("""
                UPDATE Users
                SET balance = :new_balance
                WHERE id = :user_id
            """, new_balance=new_balance, user_id=user_id)
            
            return True, new_balance
        except Exception as e:
            print(f"DEBUG: Error updating balance: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_public_info(user_id):
        """Get public user information for display"""
        rows = app.db.execute("""
            SELECT id, firstname, lastname, email, address
            FROM Users
            WHERE id = :user_id
        """, user_id=user_id)
        
        if not rows:
            return None
        
        user_data = rows[0]
        return {
            'id': user_data[0],
            'firstname': user_data[1],
            'lastname': user_data[2],
            'email': user_data[3],
            'address': user_data[4]
        }

    @staticmethod
    def is_seller(user_id):
        """Check if user is a seller (has products in inventory)"""
        rows = app.db.execute("""
            SELECT COUNT(*) FROM Inventory WHERE user_id = :user_id
        """, user_id=user_id)
        
        return rows[0][0] > 0 if rows else False
