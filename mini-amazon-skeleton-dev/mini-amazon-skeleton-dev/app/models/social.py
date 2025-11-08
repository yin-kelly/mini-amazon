from flask import current_app as app
from datetime import datetime

class ProductQuestion:
    def __init__(self, question_id, product_id, asker_id, title, content, created_at):
        self.id = question_id
        self.product_id = product_id
        self.asker_id = asker_id
        self.title = title
        self.content = content
        self.created_at = created_at

    @staticmethod
    def get_by_product(product_id, limit=10):
        """Get questions for a product with asker info"""
        rows = app.db.execute('''
            SELECT q.question_id, q.product_id, q.asker_id, q.title, q.content, q.created_at,
                   u.firstname, u.lastname
            FROM ProductQuestions q
            JOIN Users u ON q.asker_id = u.id
            WHERE q.product_id = :product_id
            ORDER BY q.created_at DESC
            LIMIT :limit
        ''', product_id=product_id, limit=limit)
        
        questions = []
        for row in rows:
            question = ProductQuestion(*row[:6])
            question.asker_name = f"{row[6]} {row[7]}"
            questions.append(question)
        
        return questions

    @staticmethod
    def create(product_id, asker_id, title, content):
        """Create a new question"""
        rows = app.db.execute('''
            INSERT INTO ProductQuestions (product_id, asker_id, title, content, created_at)
            VALUES (:product_id, :asker_id, :title, :content, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING question_id
        ''', product_id=product_id, asker_id=asker_id, title=title, content=content)
        return rows[0][0] if rows else None


class ProductAnswer:
    def __init__(self, answer_id, question_id, responder_id, content, created_at):
        self.id = answer_id
        self.question_id = question_id
        self.responder_id = responder_id
        self.content = content
        self.created_at = created_at

    @staticmethod
    def get_by_question(question_id):
        """Get answers for a question with responder info"""
        rows = app.db.execute('''
            SELECT a.answer_id, a.question_id, a.responder_id, a.content, a.created_at,
                   u.firstname, u.lastname
            FROM ProductAnswers a
            JOIN Users u ON a.responder_id = u.id
            WHERE a.question_id = :question_id
            ORDER BY a.created_at ASC
        ''', question_id=question_id)
        
        answers = []
        for row in rows:
            answer = ProductAnswer(*row[:5])
            answer.responder_name = f"{row[5]} {row[6]}"
            answers.append(answer)
        
        return answers

    @staticmethod
    def create(question_id, responder_id, content):
        """Create a new answer"""
        rows = app.db.execute('''
            INSERT INTO ProductAnswers (question_id, responder_id, content, created_at)
            VALUES (:question_id, :responder_id, :content, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING answer_id
        ''', question_id=question_id, responder_id=responder_id, content=content)
        return rows[0][0] if rows else None


class Notification:
    def __init__(self, notification_id, user_id, kind, payload, is_read, created_at):
        self.id = notification_id
        self.user_id = user_id
        self.kind = kind
        self.payload = payload
        self.is_read = is_read
        self.created_at = created_at

    @staticmethod
    def get_for_user(user_id, limit=20):
        """Get notifications for a user"""
        rows = app.db.execute('''
            SELECT notification_id, user_id, kind, payload, is_read, created_at
            FROM Notifications
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        ''', user_id=user_id, limit=limit)
        
        return [Notification(*row) for row in rows]

    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        rows = app.db.execute('''
            SELECT COUNT(*) FROM Notifications
            WHERE user_id = :user_id AND is_read = FALSE
        ''', user_id=user_id)
        
        return rows[0][0] if rows else 0

    @staticmethod
    def create(user_id, kind, payload):
        """Create a new notification"""
        rows = app.db.execute('''
            INSERT INTO Notifications (user_id, kind, payload, is_read, created_at)
            VALUES (:user_id, :kind, :payload, FALSE, (current_timestamp AT TIME ZONE 'UTC'))
            RETURNING notification_id
        ''', user_id=user_id, kind=kind, payload=payload)
        return rows[0][0] if rows else None

    @staticmethod
    def mark_read(notification_id, user_id):
        """Mark a notification as read"""
        app.db.execute('''
            UPDATE Notifications 
            SET is_read = TRUE 
            WHERE notification_id = :notification_id AND user_id = :user_id
        ''', notification_id=notification_id, user_id=user_id)

    @staticmethod
    def mark_all_read(user_id):
        """Mark all notifications as read for a user"""
        app.db.execute('''
            UPDATE Notifications 
            SET is_read = TRUE 
            WHERE user_id = :user_id AND is_read = FALSE
        ''', user_id=user_id)
