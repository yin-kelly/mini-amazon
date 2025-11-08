-- Add new features: messaging, upvotes, and review images
-- NOTE: We cannot enforce "sender must be buyer or seller" with a CHECK subquery in Postgres.
--       We’ll enforce that in application code (or via a trigger later if desired).

-- Message Threads Table
CREATE TABLE IF NOT EXISTS MessageThreads (
    thread_id     SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES Orders(order_id) ON DELETE CASCADE,
    buyer_id      INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    seller_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                  DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    CONSTRAINT message_threads_one_per_order_seller UNIQUE (order_id, seller_id)
);

-- Messages Table
CREATE TABLE IF NOT EXISTS Messages (
    message_id    SERIAL PRIMARY KEY,
    thread_id     INT NOT NULL REFERENCES MessageThreads(thread_id) ON DELETE CASCADE,
    sender_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    content       TEXT NOT NULL,
    created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                  DEFAULT (current_timestamp AT TIME ZONE 'UTC')
    -- App-layer rule: sender_id must equal buyer_id or seller_id of this thread.
);

-- Review Upvotes Table
CREATE TABLE IF NOT EXISTS ReviewUpvotes (
    upvote_id     SERIAL PRIMARY KEY,
    review_id     INT NOT NULL,
    review_type   VARCHAR(10) NOT NULL CHECK (review_type IN ('product', 'seller')),
    user_id       INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    created_at    TIMESTAMP WITHOUT TIME ZONE NOT NULL
                  DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    CONSTRAINT review_upvotes_one_per_user_per_review UNIQUE (review_id, review_type, user_id)
);

-- Review Images Table
CREATE TABLE IF NOT EXISTS ReviewImages (
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
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON Messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON Messages(created_at);
CREATE INDEX IF NOT EXISTS idx_review_upvotes_review ON ReviewUpvotes(review_id, review_type);

-- Product Q&A
CREATE TABLE IF NOT EXISTS ProductQuestions (
    question_id  SERIAL PRIMARY KEY,
    product_id   INT NOT NULL REFERENCES Products(product_id) ON DELETE CASCADE,
    asker_id     INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    title        VARCHAR(120) NOT NULL,
    content      VARCHAR(500) NOT NULL,
    created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL
                 DEFAULT (current_timestamp AT TIME ZONE 'UTC')
);

CREATE TABLE IF NOT EXISTS ProductAnswers (
    answer_id    SERIAL PRIMARY KEY,
    question_id  INT NOT NULL REFERENCES ProductQuestions(question_id) ON DELETE CASCADE,
    responder_id INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    content      VARCHAR(800) NOT NULL,
    created_at   TIMESTAMP WITHOUT TIME ZONE NOT NULL
                 DEFAULT (current_timestamp AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_product_questions_product ON ProductQuestions(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_answers_question ON ProductAnswers(question_id, created_at ASC);

-- In-site Notifications
CREATE TABLE IF NOT EXISTS Notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    kind            VARCHAR(30) NOT NULL, -- 'message', 'upvote', 'answer'
    payload         JSONB NOT NULL,       -- {thread_id,...} or {review_id,...} etc.
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP WITHOUT TIME ZONE NOT NULL
                    DEFAULT (current_timestamp AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON Notifications(user_id, is_read, created_at DESC);