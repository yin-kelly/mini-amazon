from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models.wish import Wish
from .models.product import Product

bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@bp.route('', methods=['GET'])
@login_required
def wishlist():
    """Show user's wishlist"""
    items = Wish.get_all_by_uid(current_user.id)
    
    # Get product details for each wishlist item
    product_map = {}
    for item in items:
        if item.product_id not in product_map:
            product = Product.get(item.product_id)
            product_map[item.product_id] = product
    
    return render_template('wishlist.html', items=items, product_map=product_map)

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    """Add a product to user's wishlist"""
    success = Wish.add(current_user.id, product_id)
    if success:
        flash('Product added to wishlist!', 'success')
    else:
        flash('Product is already in your wishlist!', 'info')
    
    return redirect(url_for('wishlist.wishlist'))

@bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    """Remove a product from user's wishlist"""
    Wish.remove(current_user.id, product_id)
    flash('Product removed from wishlist!', 'success')
    return redirect(url_for('wishlist.wishlist'))
