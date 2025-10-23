-- Add ProductReviews table to existing database
-- Run this if you want to enable reviews functionality

CREATE TABLE IF NOT EXISTS ProductReviews (
    review_id   SERIAL PRIMARY KEY,
    product_id  INT NOT NULL REFERENCES Products(product_id),
    user_id     INT NOT NULL REFERENCES Users(id),
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    feedback    VARCHAR(300),
    created_at  TIMESTAMP WITHOUT TIME ZONE NOT NULL
                DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    CONSTRAINT product_reviews_one_per_pair UNIQUE (product_id, user_id)
);

-- Add some sample reviews for testing
INSERT INTO ProductReviews (product_id, user_id, rating, feedback) VALUES
(1, 1, 5, 'Excellent product! Great build quality and fast shipping.'),
(1, 2, 4, 'Good value for money. Works as expected.'),
(1, 3, 5, 'Perfect for my needs. Fast delivery and great customer service.'),
(2, 1, 4, 'Solid product, minor issues with packaging but overall satisfied.'),
(2, 2, 3, 'Average quality, could be better for the price.')
ON CONFLICT (product_id, user_id) DO NOTHING;
