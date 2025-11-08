# Migration script to create new tables in correct order
# Run this with: python migrate_ordered.py

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import DB

def run_migration():
    app = create_app()
    with app.app_context():
        db = DB(app)
        
        # Define tables in dependency order
        tables = [
            # Core tables first
            """CREATE TABLE IF NOT EXISTS MessageThreads (
                thread_id     SERIAL PRIMARY KEY,
                order_id      INT NOT NULL REFERENCES Orders(order_id) ON DELETE CASCADE,
                buyer_id      INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                seller_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                              DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
                CONSTRAINT message_threads_one_per_order_seller UNIQUE (order_id, seller_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS Messages (
                message_id    SERIAL PRIMARY KEY,
                thread_id     INT NOT NULL REFERENCES MessageThreads(thread_id) ON DELETE CASCADE,
                sender_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                content       TEXT NOT NULL,
                created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                              DEFAULT (current_timestamp AT TIME ZONE 'UTC')
            )""",
            
            """CREATE TABLE IF NOT EXISTS ReviewUpvotes (
                upvote_id     SERIAL PRIMARY KEY,
                review_id     INT NOT NULL,
                review_type   VARCHAR(10) NOT NULL CHECK (review_type IN ('product', 'seller')),
                user_id       INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                              DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
                CONSTRAINT review_upvotes_one_per_user_per_review UNIQUE (review_id, review_type, user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS ReviewImages (
                image_id      SERIAL PRIMARY KEY,
                review_id     INT NOT NULL,
                review_type   VARCHAR(10) NOT NULL CHECK (review_type IN ('product', 'seller')),
                filename      VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_path     VARCHAR(500) NOT NULL,
                file_size     INT NOT NULL,
                mime_type     VARCHAR(100) NOT NULL,
                created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                              DEFAULT (current_timestamp AT TIME ZONE 'UTC')
            )""",
            
            """CREATE TABLE IF NOT EXISTS ProductQuestions (
                question_id  SERIAL PRIMARY KEY,
                product_id   INT NOT NULL REFERENCES Products(product_id) ON DELETE CASCADE,
                asker_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                title        VARCHAR(120) NOT NULL,
                content      VARCHAR(500) NOT NULL,
                created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL
                             DEFAULT (current_timestamp AT TIME ZONE 'UTC')
            )""",
            
            """CREATE TABLE IF NOT EXISTS ProductAnswers (
                answer_id    SERIAL PRIMARY KEY,
                question_id  INT NOT NULL REFERENCES ProductQuestions(question_id) ON DELETE CASCADE,
                responder_id INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                content      VARCHAR(800) NOT NULL,
                created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL
                             DEFAULT (current_timestamp AT TIME ZONE 'UTC')
            )""",
            
            """CREATE TABLE IF NOT EXISTS Notifications (
                notification_id SERIAL PRIMARY KEY,
                user_id         INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
                kind            VARCHAR(30) NOT NULL,
                payload         JSONB NOT NULL,
                is_read         BOOLEAN NOT NULL DEFAULT FALSE,
                created_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL
                                DEFAULT (current_timestamp AT TIME ZONE 'UTC')
            )"""
        ]
        
        # Execute table creation
        for table_sql in tables:
            try:
                db.execute(table_sql)
                table_name = table_sql.split('(')[0].split()[-1]
                print(f'✓ Created table: {table_name}')
            except Exception as e:
                print(f'✗ Error creating table: {e}')
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON Messages(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON Messages(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_review_upvotes_review ON ReviewUpvotes(review_id, review_type)",
            "CREATE INDEX IF NOT EXISTS idx_product_questions_product ON ProductQuestions(product_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_product_answers_question ON ProductAnswers(question_id, created_at ASC)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON Notifications(user_id, is_read, created_at DESC)"
        ]
        
        for index_sql in indexes:
            try:
                db.execute(index_sql)
                print(f'✓ Created index')
            except Exception as e:
                print(f'✗ Error creating index: {e}')
        
        print('Migration completed successfully!')

if __name__ == '__main__':
    run_migration()
