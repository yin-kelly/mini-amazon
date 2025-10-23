\COPY Users(id, email, password, firstname, lastname) FROM '/home/ubuntu/shared/mini-amazon-skeleton/db/data/Users.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Products(product_id, name, price, description, seller_id, available, image, category) FROM '/home/ubuntu/shared/mini-amazon-skeleton/db/data/Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_product_id_seq',
                         (SELECT MAX(product_id)+1 FROM Products),
                         false);

\COPY Purchases(id, uid, pid, time_purchased) FROM '/home/ubuntu/shared/mini-amazon-skeleton/db/data/Purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false);

\COPY Wishes(uid, product_id, time_added) FROM '/home/ubuntu/shared/mini-amazon-skeleton/db/data/Wishes.csv' WITH DELIMITER ',' NULL '' CSV HEADER
SELECT pg_catalog.setval('public.wishes_id_seq',
                         (SELECT MAX(id)+1 FROM Wishes),
                         false);