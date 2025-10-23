from flask import current_app as app
from datetime import datetime

class ProductReview:
    def __init__(self, review_id, product_id, user_id, rating, feedback, created_at):
        self.id = review_id  # Map review_id to id for template compatibility
        self.product_id = product_id
        self.user_id = user_id
        self.rating = rating
        self.title = "Review"  # Default title since schema doesn't have title
        self.content = feedback or "No review text provided"
        self.created_at = created_at

    @staticmethod
    def get_by_product(product_id):
        """Get all reviews for a product with user info"""
        rows = app.db.execute('''
SELECT r.review_id, r.product_id, r.user_id, r.rating, r.feedback, r.created_at,
       u.firstname, u.lastname
FROM ProductReviews r
JOIN Users u ON r.user_id = u.id
WHERE r.product_id = :product_id
ORDER BY r.created_at DESC
''', product_id=product_id)
        
        reviews = []
        for row in rows:
            review = ProductReview(*row[:6])
            review.user_name = f"{row[6]} {row[7]}"
            reviews.append(review)
        
        return reviews

    @staticmethod
    def get_average_rating(product_id):
        """Get average rating for a product"""
        rows = app.db.execute('''
SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        
        if rows and rows[0][0]:
            return round(float(rows[0][0]), 1), rows[0][1]
        return 0.0, 0

    @staticmethod
    def create(product_id, user_id, rating, feedback):
        """Create a new review"""
        rows = app.db.execute('''
INSERT INTO ProductReviews (product_id, user_id, rating, feedback, created_at)
VALUES (:product_id, :user_id, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
RETURNING review_id
''', product_id=product_id, user_id=user_id, rating=rating, feedback=feedback)
        return rows[0][0] if rows else None
    
class ReviewRow:
    def __init__(self, kind, target_id, target_name, rating, feedback, created_at):
        self.kind = kind              # 'product' or 'seller'
        self.target_id = target_id    # product_id or seller_id
        self.target_name = target_name
        self.rating = rating
        self.feedback = feedback
        self.created_at = created_at

class Review:
    @staticmethod
    def get_recent_by_user(uid, limit=5, kind=None, sort="date"):
        parts = []
        if kind in (None, "product"):
            parts.append("""
                SELECT 'product' AS kind,
                       pr.product_id AS target_id,
                       p.name       AS target_name,
                       pr.rating, pr.feedback, pr.created_at
                FROM ProductReviews pr
                JOIN Products p ON p.product_id = pr.product_id
                WHERE pr.user_id = :uid
            """)
        if kind in (None, "seller"):
            parts.append("""
                SELECT 'seller' AS kind,
                       sr.seller_id AS target_id,
                       (u.firstname || ' ' || u.lastname) AS target_name,
                       sr.rating, sr.feedback, sr.created_at
                FROM SellerReviews sr
                JOIN Users u ON u.id = sr.seller_id
                WHERE sr.reviewer_id = :uid
            """)
        order_clause = "created_at DESC" if sort == "date" else "rating DESC, created_at DESC"
        sql = f"{' UNION ALL '.join(parts)} ORDER BY {order_clause} LIMIT :limit"
        rows = app.db.execute(sql, uid=uid, limit=limit)
        return [ReviewRow(*r) for r in rows]
