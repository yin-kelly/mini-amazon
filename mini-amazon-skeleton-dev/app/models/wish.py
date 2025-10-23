from flask import current_app as app
from datetime import datetime

class Wish:
    def __init__(self, id, uid, product_id, time_added):
        self.id = id
        self.uid = uid
        self.product_id = product_id
        self.time_added = time_added

    @staticmethod
    def get_all_by_uid(uid):
        """Get all wishlist items for a user"""
        rows = app.db.execute('''
SELECT id, uid, product_id, time_added
FROM Wishes
WHERE uid = :uid
ORDER BY time_added DESC
''', uid=uid)
        return [Wish(*row) for row in rows]

    @staticmethod
    def add(uid, product_id):
        """Add a product to user's wishlist"""
        try:
            app.db.execute('''
INSERT INTO Wishes (uid, product_id, time_added)
VALUES (:uid, :product_id, (current_timestamp AT TIME ZONE 'UTC'))
''', uid=uid, product_id=product_id)
            return True
        except Exception:
            # Product already in wishlist (unique constraint violation)
            return False

    @staticmethod
    def remove(uid, product_id):
        """Remove a product from user's wishlist"""
        app.db.execute('''
DELETE FROM Wishes
WHERE uid = :uid AND product_id = :product_id
''', uid=uid, product_id=product_id)
        return True
