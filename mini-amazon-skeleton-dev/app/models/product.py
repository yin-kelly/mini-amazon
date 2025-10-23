from flask import current_app as app

class Product:
    def __init__(self, product_id, name, price, available, description=None, image=None, category=None, avg_rating=0, total_sales=0):
        
        self.product_id = product_id
        self.id = product_id
        self.name = name
        self.price = price
        self.available = available
        self.description = description  
        self.image = image or ""
        self.category = category or ""
        self.avg_rating = float(avg_rating) if avg_rating else 0.0
        self.total_sales = int(total_sales) if total_sales else 0

    @staticmethod
    def get(product_id):
        rows = app.db.execute('''
SELECT p.product_id, p.name, p.price, p.available, p.description, COALESCE(p.image, '') AS image, COALESCE(p.category, '') AS category,
       COALESCE(u.firstname || ' ' || u.lastname, 'Unknown Seller') AS seller_name
FROM Products p
LEFT JOIN Users u ON p.seller_id = u.id
WHERE p.product_id = :product_id
''',
                              product_id=product_id)
        if rows:
            product = Product(*rows[0][:7])
            product.seller_name = rows[0][7]
            return product
        return None

    @staticmethod
    def get_all(available=True, sort: str = "name_asc", category: str | None = None):
        # our whitelist supported sort options to prevent SQL injection
        sort_map = {
            "name_asc": "name ASC",
            "name_desc": "name DESC",
            "price_asc": "price ASC",
            "price_desc": "price DESC",
            "rating_asc": "avg_rating ASC NULLS LAST",
            "rating_desc": "avg_rating DESC NULLS LAST",
            "sales_asc": "total_sales ASC NULLS LAST",
            "sales_desc": "total_sales DESC NULLS LAST",
        }
        order_clause = sort_map.get(sort, "name ASC")

        base = '''
SELECT p.product_id, p.name, p.price, p.available, p.description, COALESCE(p.image, '') AS image, COALESCE(p.category, '') AS category,
       COALESCE(u.firstname || ' ' || u.lastname, 'Unknown Seller') AS seller_name,
       COALESCE(pr.avg_rating, 0) AS avg_rating,
       COALESCE(oi.total_sales, 0) AS total_sales
FROM Products p
LEFT JOIN Users u ON p.seller_id = u.id
LEFT JOIN (
    SELECT product_id, AVG(rating) AS avg_rating
    FROM ProductReviews
    GROUP BY product_id
) pr ON p.product_id = pr.product_id
LEFT JOIN (
    SELECT i.product_id, COUNT(oi.order_id) AS total_sales
    FROM OrderItems oi
    JOIN Inventory i ON oi.inventory_id = i.inventory_id
    GROUP BY i.product_id
) oi ON p.product_id = oi.product_id
WHERE p.available = :available
'''
        params = {"available": available}
        if category and category.lower() != 'all':
            base += " AND p.category = :category\n"
            params["category"] = category
        base += f"ORDER BY {order_clause}\n"
        rows = app.db.execute(base, **params)
        
        products = []
        for row in rows:
            product = Product(*row[:7], row[8] if len(row) > 8 else 0, row[9] if len(row) > 9 else 0)
            product.seller_name = row[7]
            products.append(product)
        return products

    @staticmethod
    def get_categories():
        rows = app.db.execute('''
SELECT DISTINCT category
FROM Products
WHERE category IS NOT NULL AND category <> ''
ORDER BY category ASC
''')
        return [r[0] for r in rows]

    @staticmethod
    def create(name, description, price, seller_id, category=None, image=None):
        """Create a new product and return the product_id"""
        rows = app.db.execute('''
INSERT INTO Products (name, description, price, seller_id, category, image, available)
VALUES (:name, :description, :price, :seller_id, :category, :image, TRUE)
RETURNING product_id
''', name=name, description=description, price=price, seller_id=seller_id, 
            category=category, image=image)
        return rows[0][0] if rows else None

    @staticmethod
    def search(query):
        """Search products by name and description"""
        search_term = f"%{query}%"
        rows = app.db.execute('''
SELECT p.product_id, p.name, p.price, p.available, p.description, COALESCE(p.image, '') AS image, COALESCE(p.category, '') AS category,
       COALESCE(u.firstname || ' ' || u.lastname, 'Unknown Seller') AS seller_name,
       COALESCE(pr.avg_rating, 0) AS avg_rating,
       COALESCE(oi.total_sales, 0) AS total_sales
FROM Products p
LEFT JOIN Users u ON p.seller_id = u.id
LEFT JOIN (
    SELECT product_id, AVG(rating) AS avg_rating
    FROM ProductReviews
    GROUP BY product_id
) pr ON p.product_id = pr.product_id
LEFT JOIN (
    SELECT i.product_id, COUNT(oi.order_id) AS total_sales
    FROM OrderItems oi
    JOIN Inventory i ON oi.inventory_id = i.inventory_id
    GROUP BY i.product_id
) oi ON p.product_id = oi.product_id
WHERE p.available = TRUE 
  AND (LOWER(p.name) LIKE LOWER(:query) OR LOWER(p.description) LIKE LOWER(:query))
ORDER BY p.name ASC
''', query=search_term)
        
        products = []
        for row in rows:
            product = Product(*row[:7], row[8] if len(row) > 8 else 0, row[9] if len(row) > 9 else 0)
            product.seller_name = row[7]
            products.append(product)
        return products

    @staticmethod
    def update(product_id, name, description=None, category=None, image=None):
        """Update product information"""
        app.db.execute('''
            UPDATE Products 
            SET name = :name, description = :description, category = :category, image = :image
            WHERE product_id = :product_id
        ''', product_id=product_id, name=name, description=description, category=category, image=image)
        return True