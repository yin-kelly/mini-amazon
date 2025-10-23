# app/sellers.py
from flask import Blueprint, render_template, redirect, url_for, request
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


