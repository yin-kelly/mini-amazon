# app/cart.py
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, current_app, abort, jsonify
)
from flask_login import current_user, login_required

from .models.cart import Cart

bp = Blueprint("cart", __name__)

# --- helpers ---------------------------------------------------------------

def _ensure_cart_id(user_id: int) -> int:
    return Cart.ensure_for_user(user_id)

def _resolve_inventory_id_for_product(product_id: int) -> int | None:
    """
    With your design (each product is a single seller listing),
    map product_id -> its lone inventory row.

    NOTE: DB.execute takes only one SQL string; no params dict.
    """
    rows = current_app.db.execute(f"""
        SELECT inventory_id
        FROM Inventory
        WHERE product_id = {product_id}
        ORDER BY inventory_id ASC
    """)
    return rows[0][0] if rows else None

# --- routes ----------------------------------------------------------------

@bp.route("/cart")
@login_required
def cart_page():
    cart_id = _ensure_cart_id(current_user.id)
    items = Cart.get_items(cart_id)
    subtotal, _ = Cart.totals(cart_id)
    return render_template("cart.html", items=items, cart_total=subtotal)

@bp.route("/cart/<int:user_id>")
@login_required
def cart_api(user_id: int):
    if user_id != current_user.id:
        abort(403)
    cart_id = _ensure_cart_id(user_id)
    return jsonify(Cart.get_items(cart_id))

@bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id: int):
    qty = int(request.form.get("quantity", 1))
    if qty <= 0:
        return redirect(url_for("cart.cart_page"))

    inventory_id = _resolve_inventory_id_for_product(product_id)
    if inventory_id is None:
        return redirect(url_for("cart.cart_page"))

    cart_id = _ensure_cart_id(current_user.id)
    Cart.add_item(cart_id, inventory_id, qty)
    return redirect(url_for("cart.cart_page"))

@bp.route("/cart/update", methods=["POST"])
@login_required
def cart_update():
    cart_item_id = int(request.form.get("cart_item_id", 0))
    qty = int(request.form.get("quantity", 0))
    if cart_item_id > 0:
        Cart.update_qty(cart_item_id, qty)
    return redirect(url_for("cart.cart_page"))

@bp.route("/cart/remove", methods=["POST"])
@login_required
def cart_remove():
    cart_item_id = int(request.form.get("cart_item_id", 0))
    if cart_item_id > 0:
        Cart.remove_item(cart_item_id)
    return redirect(url_for("cart.cart_page"))