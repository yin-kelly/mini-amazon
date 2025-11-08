# app/sellers.py
from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from .models.inventory import Inventory
from .models.product import Product

bp = Blueprint('seller', __name__, url_prefix='/seller')

@bp.route('', methods=['GET'])
@login_required
def index():
    """
    GET /seller  -> show seller dashboard (inventory).
    Note: route '' + url_prefix '/seller' produces '/seller'.
    """
    # Clear any wishlist-related flash messages when entering seller dashboard
    from flask import session
    if '_flashes' in session:
        # Filter out wishlist messages
        filtered_flashes = []
        for category, message in session['_flashes']:
            if 'wishlist' not in message.lower():
                filtered_flashes.append((category, message))
        session['_flashes'] = filtered_flashes
    
    # inventory rows for this seller
    items = Inventory.get_by_seller(current_user.id)

    # build quick product lookup so template can show product name/description
    # Product.get(product_id) returns a Product object
    product_map = {}
    for inv in items:
        if inv.product_id not in product_map:
            p = Product.get(inv.product_id)
            product_map[inv.product_id] = p

    return render_template('seller.html', items=items, product_map=product_map)

@bp.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))
    price = float(request.form.get('price'))
    Inventory.add(current_user.id, product_id, quantity, price)
    return redirect(url_for('seller.index'))

@bp.route('/product/create', methods=['POST'])
@login_required
def create_product():
    """Create a new product and add it to seller's inventory"""
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock', 1))
    category = request.form.get('category') or None
    image = request.form.get('image') or None
    
    # Create the product
    product_id = Product.create(
        name=name,
        description=description, 
        price=price,
        seller_id=current_user.id,
        category=category,
        image=image
    )
    
    # Add to seller's inventory
    if product_id:
        Inventory.add(current_user.id, product_id, stock, price)
    
    return redirect(url_for('seller.index'))

@bp.route('/inventory/<int:inventory_id>/view')
@login_required
def view_inventory_item(inventory_id):
    """View inventory item details"""
    # Get the inventory item
    items = Inventory.get_by_seller(current_user.id)
    inventory_item = None
    for item in items:
        if item.inventory_id == inventory_id:
            inventory_item = item
            break
    
    if not inventory_item:
        return "Inventory item not found", 404
    
    # Get product details
    product = Product.get(inventory_item.product_id)
    
    return render_template('inventory_detail.html', 
                         inventory_item=inventory_item, 
                         product=product)

@bp.route('/inventory/<int:inventory_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory_item(inventory_id):
    """Edit inventory item"""
    # Get the inventory item
    items = Inventory.get_by_seller(current_user.id)
    inventory_item = None
    for item in items:
        if item.inventory_id == inventory_id:
            inventory_item = item
            break
    
    if not inventory_item:
        return "Inventory item not found", 404
    
    # Get product details
    product = Product.get(inventory_item.product_id)
    
    if request.method == 'POST':
        from flask import flash
        
        try:
            # Update product information
            name = request.form['name']
            description = request.form.get('description', '')
            category = request.form.get('category', '')
            image = request.form.get('image', '')
            
            # Update inventory information
            new_quantity = int(request.form.get('quantity'))
            new_price = float(request.form.get('price'))
            
            # Update both product and inventory
            Product.update(inventory_item.product_id, name, description, category, image)
            Inventory.update(inventory_id, new_quantity, new_price)
            
            flash('Product and inventory updated successfully!', 'success')
            return redirect(url_for('seller.index'))
            
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
    
    return render_template('edit_inventory.html', 
                         inventory_item=inventory_item, 
                         product=product)

@bp.route('/inventory/<int:inventory_id>/delete', methods=['POST'])
@login_required
def delete_inventory_item(inventory_id):
    """Delete inventory item"""
    from flask import flash
    
    # Verify the inventory item belongs to current user
    items = Inventory.get_by_seller(current_user.id)
    inventory_item = None
    for item in items:
        if item.inventory_id == inventory_id:
            inventory_item = item
            break
    
    if not inventory_item:
        return "Inventory item not found", 404
    
    
    # Delete the inventory item
    try:
        Inventory.delete(inventory_id)
        flash('Inventory item deleted successfully.', 'success')
    except Exception as e:
        flash('Error deleting inventory item. It may be referenced by existing orders.', 'error')
    
    return redirect(url_for('seller.index'))


@bp.route('/orders')
@login_required
def orders():
    """Show orders that contain this seller's products"""
    # Get all order items where this seller's inventory is involved
    rows = current_app.db.execute('''
        SELECT DISTINCT
            o.order_id,
            o.time_ordered,
            o.user_id AS buyer_id,
            u.firstname || ' ' || u.lastname AS buyer_name,
            u.address AS delivery_address,
            COUNT(oi.order_item_id) AS item_count,
            SUM(CASE WHEN oi.individual_fulfillment = 'Fulfilled' THEN 1 ELSE 0 END) AS fulfilled_count
        FROM Orders o
        JOIN OrderItems oi ON o.order_id = oi.order_id
        JOIN Inventory i ON oi.inventory_id = i.inventory_id
        JOIN Users u ON o.user_id = u.id
        WHERE i.user_id = :seller_id
        GROUP BY o.order_id, o.time_ordered, o.user_id, u.firstname, u.lastname, u.address
        ORDER BY o.time_ordered DESC
    ''', seller_id=current_user.id)
    
    orders = []
    for row in rows:
        order_id, time_ordered, buyer_id, buyer_name, delivery_address, item_count, fulfilled_count = row
        status = 'Fulfilled' if item_count == fulfilled_count else 'Pending'
        orders.append({
            'order_id': order_id,
            'time_ordered': time_ordered,
            'buyer_id': buyer_id,
            'buyer_name': buyer_name,
            'delivery_address': delivery_address,
            'item_count': item_count,
            'fulfilled_count': fulfilled_count,
            'status': status
        })
    
    return render_template('seller_orders.html', orders=orders)

@bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Show detailed view of a specific order (only items from this seller)"""
    # Get order items for this seller only
    rows = current_app.db.execute('''
        SELECT
            oi.order_item_id,
            p.product_id,
            p.name AS product_name,
            oi.quantity_required,
            oi.final_unit_price,
            oi.individual_fulfillment,
            o.user_id AS buyer_id,
            u.firstname || ' ' || u.lastname AS buyer_name,
            u.address AS delivery_address,
            o.time_ordered
        FROM OrderItems oi
        JOIN Inventory i ON oi.inventory_id = i.inventory_id
        JOIN Products p ON i.product_id = p.product_id
        JOIN Orders o ON oi.order_id = o.order_id
        JOIN Users u ON o.user_id = u.id
        WHERE oi.order_id = :order_id AND i.user_id = :seller_id
    ''', order_id=order_id, seller_id=current_user.id)
    
    if not rows:
        return "Order not found or access denied", 404
    
    items = []
    order_info = None
    for row in rows:
        if not order_info:
            order_info = {
                'order_id': order_id,
                'buyer_name': row[7],
                'delivery_address': row[8],
                'time_ordered': row[9]
            }
        items.append({
            'order_item_id': row[0],
            'product_id': row[1],
            'product_name': row[2],
            'quantity': row[3],
            'unit_price': row[4],
            'fulfillment_status': row[5]
        })
    
    return render_template('seller_order_detail.html', order=order_info, items=items)

@bp.route('/orders/fulfill/<int:order_item_id>', methods=['POST'])
@login_required
def fulfill_item(order_item_id):
    """Mark an order item as fulfilled"""
    # Verify this order item belongs to this seller
    rows = current_app.db.execute('''
        SELECT i.user_id
        FROM OrderItems oi
        JOIN Inventory i ON oi.inventory_id = i.inventory_id
        WHERE oi.order_item_id = :order_item_id
    ''', order_item_id=order_item_id)
    
    if not rows or rows[0][0] != current_user.id:
        return "Access denied", 403
    
    # Update fulfillment status
    current_app.db.execute('''
        UPDATE OrderItems
        SET individual_fulfillment = 'Fulfilled'
        WHERE order_item_id = :order_item_id
    ''', order_item_id=order_item_id)
    
    flash('Item marked as fulfilled!', 'success')
    return redirect(request.referrer or url_for('seller.orders'))
@bp.route('/public/<int:seller_id>')
def public_seller_page(seller_id):
    """
    Public-facing seller page showing seller info and their products.
    This is the main page users see when they click on "sold by: seller"
    """
    # Get seller information
    seller_rows = current_app.db.execute('''
        SELECT id, firstname, lastname, email, address
        FROM Users
        WHERE id = :seller_id
    ''', seller_id=seller_id)
    
    if not seller_rows:
        flash('Seller not found', 'error')
        return redirect(url_for('index.index'))
    
    seller = {
        'id': seller_rows[0][0],
        'firstname': seller_rows[0][1],
        'lastname': seller_rows[0][2],
        'email': seller_rows[0][3],
        'address': seller_rows[0][4],
        'full_name': f"{seller_rows[0][1]} {seller_rows[0][2]}"
    }
    
    # Get seller's products with inventory details
    product_rows = current_app.db.execute('''
        SELECT 
            p.product_id,
            p.name,
            p.description,
            p.category,
            p.image,
            i.inventory_id,
            i.quantity,
            i.price,
            i.price_updated_at
        FROM Products p
        JOIN Inventory i ON p.product_id = i.product_id
        WHERE i.user_id = :seller_id
        AND i.quantity > 0
        ORDER BY p.name ASC
    ''', seller_id=seller_id)
    
    products = []
    for row in product_rows:
        products.append({
            'product_id': row[0],
            'name': row[1],
            'description': row[2],
            'category': row[3],
            'image': row[4],
            'inventory_id': row[5],
            'quantity': row[6],
            'price': float(row[7]),
            'price_updated_at': row[8]
        })
    
    # Get seller statistics
    stats_rows = current_app.db.execute('''
        SELECT 
            COUNT(DISTINCT i.product_id) as total_products,
            COUNT(DISTINCT oi.order_id) as total_orders,
            COALESCE(AVG(sr.rating), 0) as avg_rating,
            COUNT(DISTINCT sr.review_id) as review_count
        FROM Inventory i
        LEFT JOIN OrderItems oi ON i.inventory_id = oi.inventory_id
        LEFT JOIN SellerReviews sr ON sr.seller_id = i.user_id
        WHERE i.user_id = :seller_id
    ''', seller_id=seller_id)
    
    stats = {
        'total_products': stats_rows[0][0] or 0,
        'total_orders': stats_rows[0][1] or 0,
        'avg_rating': round(float(stats_rows[0][2] or 0), 1),
        'review_count': stats_rows[0][3] or 0
    }
    
    # Get seller reviews
    review_rows = current_app.db.execute('''
        SELECT 
            sr.review_id,
            sr.rating,
            sr.feedback,
            sr.created_at,
            u.firstname,
            u.lastname
        FROM SellerReviews sr
        JOIN Users u ON sr.reviewer_id = u.id
        WHERE sr.seller_id = :seller_id
        ORDER BY sr.created_at DESC
        LIMIT 10
    ''', seller_id=seller_id)
    
    reviews = []
    for row in review_rows:
        reviews.append({
            'review_id': row[0],
            'rating': row[1],
            'feedback': row[2] or 'No comment provided',
            'created_at': row[3],
            'reviewer_name': f"{row[4]} {row[5]}"
        })
    
    return render_template('public_seller_page.html',
                         seller=seller,
                         products=products,
                         stats=stats,
                         reviews=reviews)


@bp.route('/api/<int:seller_id>/products')
def get_seller_products_api(seller_id):
    """
    API endpoint: Returns JSON data about seller and their products.
    This demonstrates SQL execution with proper data formatting.
    """
    # Get seller basic information
    seller_rows = current_app.db.execute('''
        SELECT id, firstname, lastname, email, address
        FROM Users
        WHERE id = :seller_id
    ''', seller_id=seller_id)
    
    if not seller_rows:
        return jsonify({'error': 'Seller not found'}), 404
    
    seller_info = {
        'id': seller_rows[0][0],
        'firstname': seller_rows[0][1],
        'lastname': seller_rows[0][2],
        'full_name': f"{seller_rows[0][1]} {seller_rows[0][2]}",
        'email': seller_rows[0][3],
        'address': seller_rows[0][4]
    }
    
    # Get seller's products with inventory information
    product_rows = current_app.db.execute('''
        SELECT 
            p.product_id,
            p.name,
            p.description,
            p.category,
            p.image,
            i.inventory_id,
            i.quantity,
            i.price,
            i.price_updated_at
        FROM Products p
        JOIN Inventory i ON p.product_id = i.product_id
        WHERE i.user_id = :seller_id
        AND i.quantity > 0
        ORDER BY p.name ASC
    ''', seller_id=seller_id)
    
    # Format products
    products = []
    for row in product_rows:
        products.append({
            'product_id': row[0],
            'name': row[1],
            'description': row[2],
            'category': row[3],
            'image': row[4],
            'inventory_id': row[5],
            'quantity': row[6],
            'price': float(row[7]),
            'price_updated_at': row[8].isoformat() if row[8] else None
        })
    
    # Calculate seller statistics
    stats_rows = current_app.db.execute('''
        SELECT 
            COUNT(DISTINCT i.product_id) as total_products,
            COUNT(DISTINCT oi.order_id) as total_orders,
            COALESCE(AVG(sr.rating), 0) as avg_rating,
            COUNT(DISTINCT sr.review_id) as review_count
        FROM Inventory i
        LEFT JOIN OrderItems oi ON i.inventory_id = oi.inventory_id
        LEFT JOIN SellerReviews sr ON sr.seller_id = i.user_id
        WHERE i.user_id = :seller_id
    ''', seller_id=seller_id)
    
    stats = {
        'total_products': stats_rows[0][0] or 0,
        'total_orders': stats_rows[0][1] or 0,
        'avg_rating': round(float(stats_rows[0][2] or 0), 1),
        'review_count': stats_rows[0][3] or 0
    }
    
    return jsonify({
        'seller': seller_info,
        'products': products,
        'statistics': stats
    })
