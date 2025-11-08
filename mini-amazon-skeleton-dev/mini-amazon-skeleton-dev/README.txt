Team Members:
- Alora Orr amo55
- Meeraa Ramakrishnan mpr40
- Athena Wemmert anw62
- Kelly Yin ky132
- Burak Donbekci bd158

Project Option: Standard
Team Name: BAKMA

Milestone 2

Athena- Social Guru, created figma pages order history/review page and database design for this section (reviews)
Alora - Account/purchases Guru, created figma page and database for user
Burak - Cart Guru' created wireframe pages for cart, checkout and order completion; database design for associated section. 
Kelly - inventory, created figma pages for seller dashboard (inventory and orders) and the database design for this section (inventory)
Meeraa - products, created figma page for browsing and detailed product description as well as the database design for this section (products) 

Milestone 3 

Video link: https://drive.google.com/file/d/1kvrE1trok6Ate_QoUQcO0ugMOSQPtlwm/view?usp=sharing

Meeraa - I implemented adding a product (still working on image addition), sorting by different mechanisms (such as price, sales, etc), 
sorting by category, adding items to a wishlist, and searching in the search bar.
The code for my endpoint (sorting by price high to low) can mainly be found in: 
    - The product.get_all() method in app/models/product.py (lines 35-84)
    - Lines 50-76 build the SQL with ORDER BY {order_clause} in product.py
    - The frontend UI elements like the dropdown select can be found in app/templates/index.html (lines 23-32)
    - Finally, routing can be found in app/index.py (lines 12-42) 

Kelly - I implemented displaying a profile page for each seller showing all products in their inventory. Users can click on any seller's name throughout the site to view their page with product listings, statistics, and customer reviews.
The code for my endpoint (getting products by seller ID) is mainly in sellers.py (get_seller_products_api() and public_seller_page()) and product.py (.get() and .get_all() methods where seller_id was added). The frontend design is in public_seller_page.html.

Alora - I implemented the user purchase history system, which successfully shows a comprehensive purchase history for each user. The system displays order summaries with total amounts, item counts, fulfillment status, and links to detailed order pages. 
Users can also use the "Buy Again" functionality to re-purchase entire orders or individual items.
The code for my endpoints can mainly be found in:
    users.py - get_user_order_summaries() function and profile() route for displaying order history
    users.py - buy_again(), buy_again_product(), and buy_again_order() routes for re-purchasing functionality
    users.py - public_user_view() route for public user profiles with seller reviews
    models/user.py - get_public_info(), is_seller(), and update_balance() methods for user management
    profile.html - Order history table with status badges, action buttons, and fallback for individual purchases
    balance.html - Balance management interface for adding/withdrawing funds

Burak - I implemented the cart and checkout systems, enabling users to add products to their carts, update or remove items, and proceed through a multi-step checkout flow that finalizes orders and updates inventory in real time.
I also made contributions ensuring placed orders are recorded in the database and visible in each user’s order history with detailed confirmation pages that can be used for fullfilment and reviewing functionalities.
The code for my endpoints and logic can mainly be found in:
	•	app/models/cart.py — SQL model for carts, cart items, and total calculations
	•	app/checkout.py — handles checkout flow, order validation, and placement
	•	app/orders.py — manages order creation, storage, and detailed order display
	•	app/cart.py — implemented routes for viewing, adding, updating, and removing cart items
	•	templates/cart.html — displays user’s current cart and item management controls
	•	templates/checkout.html — checkout review and confirmation interface
	•	templates/checkout_success.html — success page after placing an order
	•	templates/checkout_error.html — error feedback for failed checkouts
	•	templates/order_confirmation.html — immediate order summary after purchase
	•	templates/order_detail.html — detailed page for an individual order with items and totals
	•	templates/orders.html — complete order history page accessible from the navbar

Athena – I implemented the reviews system, allowing users to view and submit feedback on products and sellers they’ve purchased from.

I created SQL logic to retrieve a user’s five most recent reviews and built the frontend pages where reviews are displayed and submitted, integrating these with the order details page for seamless interaction.

The code for my endpoints and logic can mainly be found in:
• app/models/review.py — SQL queries for retrieving and creating reviews
• app/reviews.py — routes for viewing and submitting user feedback
• templates/my_reviews.html and templates/review_form.html — pages for displaying and posting reviews