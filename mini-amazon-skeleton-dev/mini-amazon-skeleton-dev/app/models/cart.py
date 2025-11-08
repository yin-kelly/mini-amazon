# app/models/cart.py
from flask import current_app

class Cart:
    @staticmethod
    def ensure_for_user(user_id: int) -> int:
        """Return existing cart_id for user or create one."""
        rows = current_app.db.execute(f"""
            SELECT cart_id
            FROM Carts
            WHERE user_id = {user_id}
        """)
        if rows:
            # DB returns tuples; first column is cart_id
            return rows[0][0]

        # Create and return the new cart id
        rows = current_app.db.execute(f"""
            INSERT INTO Carts(user_id)
            VALUES ({user_id})
            RETURNING cart_id
        """)
        return rows[0][0]

    @staticmethod
    def get_items(cart_id: int):
        """
        Return cart items with joined product + seller + price info.
        Each row comes back as a tuple; map to dicts for templates/JSON.
        """
        rows = current_app.db.execute(f"""
            SELECT
                ci.cart_item_id,                 -- 0
                ci.quantity_required,            -- 1
                i.inventory_id,                  -- 2
                i.price        AS unit_price,    -- 3
                i.user_id      AS seller_id,     -- 4
                p.product_id,                    -- 5
                p.name         AS product_name,  -- 6
                p.image,                         -- 7
                p.category                        -- 8
            FROM CartItems ci
            JOIN Inventory i ON ci.inventory_id = i.inventory_id
            JOIN Products  p ON i.product_id   = p.product_id
            WHERE ci.cart_id = {cart_id}
            ORDER BY ci.cart_item_id DESC
        """)
        cols = [
            "cart_item_id", "quantity_required", "inventory_id", "unit_price",
            "seller_id", "product_id", "product_name", "image", "category"
        ]
        return [dict(zip(cols, r)) for r in rows]

    @staticmethod
    def add_item(cart_id: int, inventory_id: int, qty: int):
        """Add or bump quantity for same inventory_id in this cart."""
        # Check if an item already exists for this inventory in the cart
        rows = current_app.db.execute(f"""
            SELECT cart_item_id, quantity_required
            FROM CartItems
            WHERE cart_id = {cart_id} AND inventory_id = {inventory_id}
        """)
        if rows:
            cart_item_id, cur_qty = rows[0]
            new_qty = cur_qty + qty
            current_app.db.execute(f"""
                UPDATE CartItems
                SET quantity_required = {new_qty}
                WHERE cart_item_id = {cart_item_id}
            """)
            return cart_item_id, new_qty

        rows = current_app.db.execute(f"""
            INSERT INTO CartItems(cart_id, inventory_id, quantity_required)
            VALUES ({cart_id}, {inventory_id}, {qty})
            RETURNING cart_item_id
        """)
        return rows[0][0], qty

    @staticmethod
    def update_qty(cart_item_id: int, qty: int):
        """Set quantity; if qty <= 0, remove the item."""
        if qty <= 0:
            current_app.db.execute(f"""
                DELETE FROM CartItems
                WHERE cart_item_id = {cart_item_id}
            """)
            return
        current_app.db.execute(f"""
            UPDATE CartItems
            SET quantity_required = {qty}
            WHERE cart_item_id = {cart_item_id}
        """)

    @staticmethod
    def remove_item(cart_item_id: int):
        current_app.db.execute(f"""
            DELETE FROM CartItems
            WHERE cart_item_id = {cart_item_id}
        """)

    @staticmethod
    def clear(cart_id: int):
        current_app.db.execute(f"""
            DELETE FROM CartItems
            WHERE cart_id = {cart_id}
        """)

    @staticmethod
    def totals(cart_id: int):
        """
        Compute subtotal and total item count using current inventory prices.
        """
        rows = current_app.db.execute(f"""
            SELECT COALESCE(SUM(ci.quantity_required * i.price), 0) AS subtotal,
                   COALESCE(SUM(ci.quantity_required), 0)          AS items_count
            FROM CartItems ci
            JOIN Inventory i ON ci.inventory_id = i.inventory_id
            WHERE ci.cart_id = {cart_id}
        """)
        subtotal, items_count = rows[0]
        return float(subtotal), int(items_count)