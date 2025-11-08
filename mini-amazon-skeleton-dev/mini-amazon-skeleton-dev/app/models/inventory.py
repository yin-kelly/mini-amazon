# app/models/inventory.py
from flask import current_app as app
from datetime import datetime

class Inventory:
    def __init__(self, inventory_id, user_id, product_id, quantity, price, price_updated_at):
        self.inventory_id = inventory_id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = float(price)
        # ensure a datetime object if DB driver returns string
        self.price_updated_at = price_updated_at if isinstance(price_updated_at, datetime) else price_updated_at

    @staticmethod
    def get_by_seller(user_id):
        rows = app.db.execute('''
            SELECT inventory_id, user_id, product_id, quantity, price, price_updated_at
            FROM Inventory
            WHERE user_id = :user_id
            ORDER BY price_updated_at DESC
        ''', user_id=user_id)
        return [Inventory(*row) for row in rows]

    @staticmethod
    def add(user_id, product_id, quantity, price):
        rows = app.db.execute('''
            INSERT INTO Inventory(user_id, product_id, quantity, price, price_updated_at)
            VALUES (:user_id, :product_id, :quantity, :price, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING inventory_id
        ''', user_id=user_id, product_id=product_id, quantity=quantity, price=price)
        return rows[0][0] if rows else None

    @staticmethod
    def update(inventory_id, quantity, price):
        """Update inventory item quantity and price"""
        app.db.execute('''
            UPDATE Inventory
            SET quantity = :quantity, price = :price, price_updated_at = (current_timestamp AT TIME ZONE 'UTC')
            WHERE inventory_id = :inventory_id
        ''', inventory_id=inventory_id, quantity=quantity, price=price)
        return True


    @staticmethod
    def delete(inventory_id):
        app.db.execute('''
            DELETE FROM Inventory
            WHERE inventory_id = :inventory_id
        ''', inventory_id=inventory_id)
        return True

    @staticmethod
    def get_by_product(product_id):
        """Get all sellers who have this product in inventory"""
        rows = app.db.execute('''
            SELECT i.inventory_id, i.user_id, i.product_id, i.quantity, i.price, i.price_updated_at,
                   u.firstname, u.lastname
            FROM Inventory i
            JOIN Users u ON i.user_id = u.id
            WHERE i.product_id = :product_id AND i.quantity > 0
            ORDER BY i.price ASC
        ''', product_id=product_id)
        
        sellers = []
        for row in rows:
            inventory = Inventory(*row[:6])
            inventory.seller_name = f"{row[6]} {row[7]}"
            sellers.append(inventory)
        
        return sellers
