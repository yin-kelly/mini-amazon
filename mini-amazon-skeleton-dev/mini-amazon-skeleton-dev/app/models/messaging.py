from flask import current_app as app
from datetime import datetime

class MessageThread:
    def __init__(self, thread_id, order_id, buyer_id, seller_id, created_at):
        self.id = thread_id
        self.order_id = order_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.created_at = created_at

    @staticmethod
    def get_by_order_and_seller(order_id, seller_id):
        """Get message thread for a specific order and seller"""
        rows = app.db.execute('''
            SELECT thread_id, order_id, buyer_id, seller_id, created_at
            FROM MessageThreads
            WHERE order_id = :order_id AND seller_id = :seller_id
        ''', order_id=order_id, seller_id=seller_id)
        
        if rows:
            return MessageThread(*rows[0])
        return None

    @staticmethod
    def create(order_id, buyer_id, seller_id):
        """Create a new message thread"""
        rows = app.db.execute('''
            INSERT INTO MessageThreads (order_id, buyer_id, seller_id, created_at)
            VALUES (:order_id, :buyer_id, :seller_id, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING thread_id
        ''', order_id=order_id, buyer_id=buyer_id, seller_id=seller_id)
        return rows[0][0] if rows else None

    @staticmethod
    def get_by_user(user_id):
        """Get all message threads for a user (as buyer or seller)"""
        rows = app.db.execute('''
            SELECT mt.thread_id, mt.order_id, mt.buyer_id, mt.seller_id, mt.created_at,
                   o.time_ordered, o.status,
                   buyer.firstname || ' ' || buyer.lastname as buyer_name,
                   seller.firstname || ' ' || seller.lastname as seller_name
            FROM MessageThreads mt
            JOIN Orders o ON o.order_id = mt.order_id
            JOIN Users buyer ON buyer.id = mt.buyer_id
            JOIN Users seller ON seller.id = mt.seller_id
            WHERE mt.buyer_id = :user_id OR mt.seller_id = :user_id
            ORDER BY mt.created_at DESC
        ''', user_id=user_id)
        
        threads = []
        for row in rows:
            thread = MessageThread(*row[:5])
            thread.order_date = row[5]
            thread.order_status = row[6]
            thread.buyer_name = row[7]
            thread.seller_name = row[8]
            threads.append(thread)
        
        return threads


class Message:
    def __init__(self, message_id, thread_id, sender_id, content, created_at):
        self.id = message_id
        self.thread_id = thread_id
        self.sender_id = sender_id
        self.content = content
        self.created_at = created_at

    @staticmethod
    def get_by_thread(thread_id):
        """Get all messages for a thread"""
        rows = app.db.execute('''
            SELECT m.message_id, m.thread_id, m.sender_id, m.content, m.created_at,
                   u.firstname, u.lastname
            FROM Messages m
            JOIN Users u ON u.id = m.sender_id
            WHERE m.thread_id = :thread_id
            ORDER BY m.created_at ASC
        ''', thread_id=thread_id)
        
        messages = []
        for row in rows:
            message = Message(*row[:5])
            message.sender_name = f"{row[5]} {row[6]}"
            messages.append(message)
        
        return messages

    @staticmethod
    def create(thread_id, sender_id, content):
        """Create a new message"""
        rows = app.db.execute('''
            INSERT INTO Messages (thread_id, sender_id, content, created_at)
            VALUES (:thread_id, :sender_id, :content, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING message_id
        ''', thread_id=thread_id, sender_id=sender_id, content=content)
        return rows[0][0] if rows else None


class ReviewUpvote:
    def __init__(self, upvote_id, review_id, review_type, user_id, created_at):
        self.id = upvote_id
        self.review_id = review_id
        self.review_type = review_type
        self.user_id = user_id
        self.created_at = created_at

    @staticmethod
    def get_count(review_id, review_type):
        """Get upvote count for a review"""
        rows = app.db.execute('''
            SELECT COUNT(*) as upvote_count
            FROM ReviewUpvotes
            WHERE review_id = :review_id AND review_type = :review_type
        ''', review_id=review_id, review_type=review_type)
        
        return rows[0][0] if rows else 0

    @staticmethod
    def has_user_upvoted(review_id, review_type, user_id):
        """Check if user has upvoted a review"""
        rows = app.db.execute('''
            SELECT 1
            FROM ReviewUpvotes
            WHERE review_id = :review_id AND review_type = :review_type AND user_id = :user_id
        ''', review_id=review_id, review_type=review_type, user_id=user_id)
        
        return len(rows) > 0

    @staticmethod
    def toggle_upvote(review_id, review_type, user_id):
        """Toggle upvote for a review"""
        # Check if already upvoted
        if ReviewUpvote.has_user_upvoted(review_id, review_type, user_id):
            # Remove upvote
            app.db.execute('''
                DELETE FROM ReviewUpvotes
                WHERE review_id = :review_id AND review_type = :review_type AND user_id = :user_id
            ''', review_id=review_id, review_type=review_type, user_id=user_id)
            return False
        else:
            # Add upvote
            app.db.execute('''
                INSERT INTO ReviewUpvotes (review_id, review_type, user_id, created_at)
                VALUES (:review_id, :review_type, :user_id, (current_timestamp AT TIME ZONE 'UTC'))
            ''', review_id=review_id, review_type=review_type, user_id=user_id)
            return True


class ReviewImage:
    def __init__(self, image_id, review_id, review_type, filename, original_name, file_path, file_size, mime_type, created_at):
        self.id = image_id
        self.review_id = review_id
        self.review_type = review_type
        self.filename = filename
        self.original_name = original_name
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.created_at = created_at

    @staticmethod
    def get_by_review(review_id, review_type):
        """Get all images for a review"""
        rows = app.db.execute('''
            SELECT image_id, review_id, review_type, filename, original_name, file_path, file_size, mime_type, created_at
            FROM ReviewImages
            WHERE review_id = :review_id AND review_type = :review_type
            ORDER BY created_at ASC
        ''', review_id=review_id, review_type=review_type)
        
        return [ReviewImage(*row) for row in rows]

    @staticmethod
    def create(review_id, review_type, filename, original_name, file_path, file_size, mime_type):
        """Create a new review image record"""
        rows = app.db.execute('''
            INSERT INTO ReviewImages (review_id, review_type, filename, original_name, file_path, file_size, mime_type, created_at)
            VALUES (:review_id, :review_type, :filename, :original_name, :file_path, :file_size, :mime_type, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING image_id
        ''', review_id=review_id, review_type=review_type, filename=filename, 
             original_name=original_name, file_path=file_path, file_size=file_size, mime_type=mime_type)
        return rows[0][0] if rows else None

    @staticmethod
    def delete(image_id):
        """Delete a review image"""
        app.db.execute('''
            DELETE FROM ReviewImages WHERE image_id = :image_id
        ''', image_id=image_id)
