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
    
    # Check if we should show flash messages (not from seller dashboard)
    referrer = request.referrer
    redirect_to = request.form.get('redirect_to')
    show_flash = True
    
    # Don't show flash messages if coming from or going to seller dashboard
    if referrer and '/seller' in referrer:
        show_flash = False
    if redirect_to and '/seller' in redirect_to:
        show_flash = False
    
    if show_flash:
        if success:
            flash('Product added to wishlist!', 'success')
        else:
            flash('Product is already in your wishlist!', 'info')
    else:
        # Clear any existing flash messages if we're in seller context
        from flask import session
        session.pop('_flashes', None)
    
    # Check for explicit redirect parameter first
    if redirect_to and '/seller' not in redirect_to:
        return redirect(redirect_to)
    
    # Fallback to referrer, but avoid seller dashboard
    if referrer and ('/seller' not in referrer and '/wishlist' not in referrer):
        return redirect(referrer)
    else:
        return redirect(url_for('index.index'))

@bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    """Remove a product from user's wishlist"""
    Wish.remove(current_user.id, product_id)
    
    # Check if we should show flash messages (not from seller dashboard)
    referrer = request.referrer
    redirect_to = request.form.get('redirect_to')
    show_flash = True
    
    # Don't show flash messages if coming from or going to seller dashboard
    if referrer and '/seller' in referrer:
        show_flash = False
    if redirect_to and '/seller' in redirect_to:
        show_flash = False
    
    if show_flash:
        flash('Product removed from wishlist!', 'success')
    else:
        # Clear any existing flash messages if we're in seller context
        from flask import session
        session.pop('_flashes', None)
    
    # Check for explicit redirect parameter first
    if redirect_to and '/seller' not in redirect_to:
        return redirect(redirect_to)
    
    # Fallback to referrer, but avoid seller dashboard
    if referrer and ('/seller' not in referrer and '/wishlist' not in referrer):
        return redirect(referrer)
    else:
        return redirect(url_for('index.index'))
