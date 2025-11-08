# app/models/purchase.py
# ------------------------------------------------------------
# This model defines a Purchase class to represent items in a
# user's purchase history. In the production flow, purchase
# history should be derived from Orders and OrderItems (not the
# demo Purchases table) so that new checkouts appear.
# ------------------------------------------------------------

from flask import current_app
from datetime import datetime

class Purchase:
    def __init__(self, id, uid, pid, time_purchased, product_name=None, price=None):
        """
        Initialize a Purchase object.

        Parameters:
        - id: the unique row ID (order_item_id or purchase id)
        - uid: the ID of the user who made the purchase
        - pid: the product ID that was purchased
        - time_purchased: timestamp of when the purchase occurred
        - product_name: (optional) name of the purchased product
        - price: (optional) price (e.g., final_unit_price) at purchase time
        """
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased
        self.product_name = product_name
        self.price = price

    # ----------------------------------------------------------------------
    # Basic helper methods (demo Purchases table)
    # ----------------------------------------------------------------------

    @staticmethod
    def get(id):
        """
        Get a single purchase record by its ID from the demo Purchases table.
        Returns one Purchase object or None if not found.
        """
        rows = current_app.db.execute("""
            SELECT p.id, p.uid, p.pid, p.time_purchased, pr.name, pr.price
            FROM Purchases p
            LEFT JOIN Products pr ON p.pid = pr.product_id
            WHERE p.id = :id
        """, id=id)
        return Purchase(*rows[0]) if rows else None

    @staticmethod
    def get_all():
        """
        Get all rows in the demo Purchases table.
        """
        rows = current_app.db.execute("""
            SELECT id, uid, pid, time_purchased
            FROM Purchases
        """)
        return [Purchase(*row) for row in rows]

    # ----------------------------------------------------------------------
    # ✅ PRODUCTION: purchase history from Orders → OrderItems → Inventory → Products
    # ----------------------------------------------------------------------

    @staticmethod
    def for_user(uid: int):
        """
        Returns all order items for a given user as their purchase history.

        Pulls from Orders/OrderItems (the real checkout path), joining through
        Inventory to Products for the product id and name. Uses the order
        timestamp as time_purchased and the order item final_unit_price as price.
        """
        rows = current_app.db.execute("""
            SELECT
                oi.order_item_id      AS id,
                o.user_id             AS uid,
                inv.product_id        AS pid,
                o.time_ordered        AS time_purchased,
                pr.name               AS product_name,
                oi.final_unit_price   AS price
            FROM Orders o
            JOIN OrderItems oi ON o.order_id = oi.order_id
            JOIN Inventory  inv ON oi.inventory_id = inv.inventory_id
            JOIN Products   pr  ON pr.product_id = inv.product_id
            WHERE o.user_id = :uid
            ORDER BY o.time_ordered DESC, oi.order_item_id DESC
        """, uid=uid)

        return [Purchase(*row) for row in rows]

    # ----------------------------------------------------------------------
    # Optional helpers (still fine to keep for other pages/tools)
    # ----------------------------------------------------------------------

    @staticmethod
    def for_user_since(uid: int, since_date):
        """
        Demo helper using the Purchases table; not used by the profile page.
        """
        rows = current_app.db.execute("""
            SELECT pu.id,
                   pu.uid,
                   pu.pid,
                   pu.time_purchased,
                   pr.name,
                   pr.price
            FROM Purchases pu
            JOIN Products pr ON pr.product_id = pu.pid
            WHERE pu.uid = :uid
              AND pu.time_purchased >= :since_date
            ORDER BY pu.time_purchased DESC
        """, uid=uid, since_date=since_date)
        return [Purchase(*row) for row in rows]

    @staticmethod
    def get_all_by_uid_since(uid, since=None):
        """
        Demo helper using the Purchases table; not used by the profile page.
        """
        if since is None:
            since = datetime.min
        rows = current_app.db.execute("""
            SELECT pu.id,
                   pu.uid,
                   pu.pid,
                   pu.time_purchased,
                   pr.name AS product_name,
                   pr.price AS price
            FROM Purchases pu
            JOIN Products pr ON pr.product_id = pu.pid
            WHERE pu.uid = :uid
              AND pu.time_purchased >= :since
            ORDER BY pu.time_purchased DESC
        """, uid=uid, since=since)
        return [Purchase(*row) for row in rows]
