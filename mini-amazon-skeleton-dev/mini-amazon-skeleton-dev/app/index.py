from flask import render_template, request, redirect, url_for
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    # get all available products for sale:
    sort = request.args.get('sort', default='name_asc')
    category = request.args.get('category', default='all')
    products = Product.get_all(True, sort=sort, category=category)
    categories = ['all'] + Product.get_categories()

    # find the products current user has bought:
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
    else:
        purchases = None

    # render the page by adding information to the index.html file
    return render_template(
        'index.html',
        avail_products=products,
        purchase_history=purchases,
        current_sort=sort,
        current_category=category,
        categories=categories
    )


@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Show detailed product page with reviews and a single 'Add to Cart' target."""
    product = Product.get(product_id)
    if not product:
        return "Product not found", 404

    # We’re doing single-listing pages, so just grab one inventory row for this product.
    # (Your Inventory.get_by_product should return at least one row when in stock.)
    from .models.inventory import Inventory
    inv_rows = Inventory.get_by_product(product_id)

    # Normalize whatever Inventory returns into an inventory_id for the add-to-cart target
    inventory_id_for_add = None
    if inv_rows:
        first = inv_rows[0]
        # try dict -> object -> tuple, in that order
        if isinstance(first, dict):
            inventory_id_for_add = first.get("inventory_id")
        else:
            inventory_id_for_add = getattr(first, "inventory_id", None)
            if inventory_id_for_add is None and isinstance(first, (list, tuple)) and len(first) > 0:
                inventory_id_for_add = first[0]

    # Reviews (optional)
    reviews = []
    try:
        from .models.review import ProductReview
        reviews = ProductReview.get_by_product(product_id)
    except Exception:
        reviews = []

    return render_template(
        'product_detail.html',
        product=product,
        reviews=reviews,
        inventory_id_for_add=inventory_id_for_add
    )


@bp.route('/search')
def search():
    """Search products by name and description"""
    query = request.args.get('q', '').strip()

    if not query:
        # If no search query, redirect to browse products
        return redirect(url_for('index.index'))

    # Search products by name and description
    products = Product.search(query)
    categories = ['all'] + Product.get_categories()

    return render_template(
        'search_results.html',
        products=products,
        query=query,
        categories=categories
    )