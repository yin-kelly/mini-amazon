from flask import current_app as app
from datetime import datetime

class SellerReview:
    def __init__(self, review_id, reviewer_id, seller_id, rating, feedback, created_at):
        self.id = review_id
        self.reviewer_id = reviewer_id
        self.seller_id = seller_id
        self.rating = rating
        self.feedback = feedback or "No review text provided"
        self.created_at = created_at

    @staticmethod
    def get_by_seller(seller_id):
        """Get all reviews for a seller with reviewer info"""
        rows = app.db.execute('''
            SELECT sr.review_id, sr.reviewer_id, sr.seller_id, sr.rating, sr.feedback, sr.created_at,
                   u.firstname, u.lastname
            FROM SellerReviews sr
            JOIN Users u ON sr.reviewer_id = u.id
            WHERE sr.seller_id = :seller_id
            ORDER BY sr.created_at DESC
        ''', seller_id=seller_id)
        
        reviews = []
        for row in rows:
            review = SellerReview(*row[:6])
            review.reviewer_name = f"{row[6]} {row[7]}"
            reviews.append(review)
        
        return reviews

    @staticmethod
    def get_average_rating(seller_id):
        """Get average rating for a seller"""
        rows = app.db.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM SellerReviews
            WHERE seller_id = :seller_id
        ''', seller_id=seller_id)
        
        if rows and rows[0][0]:
            return round(float(rows[0][0]), 1), rows[0][1]
        return 0.0, 0

    @staticmethod
    def create(seller_id, reviewer_id, rating, feedback):
        """Create a new seller review"""
        rows = app.db.execute('''
            INSERT INTO SellerReviews (seller_id, reviewer_id, rating, feedback, created_at)
            VALUES (:seller_id, :reviewer_id, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING review_id
        ''', seller_id=seller_id, reviewer_id=reviewer_id, rating=rating, feedback=feedback)
        return rows[0][0] if rows else None
