# app/checkout.py
from flask import Blueprint, render_template, redirect, url_for, current_app, request
from flask_login import login_required, current_user
from .models.cart import Cart

bp = Blueprint("checkout", __name__)

def _validate_cart_for_checkout(cart_id: int):
    """
    Build a row per cart item using *current* inventory snapshot.
    Always include current_price and available_qty even when not ok.
    Returns (validated_rows, subtotal_ok_items)
    """
    rows = current_app.db.execute(f"""
        SELECT
          ci.cart_item_id,
          ci.quantity_required       AS requested_qty,
          i.inventory_id,
          i.user_id                  AS seller_id,
          i.product_id,
          i.price                    AS current_price,
          i.quantity                 AS available_qty,
          p.name                     AS product_name,
          p.image
        FROM CartItems ci
        JOIN Inventory i ON i.inventory_id = ci.inventory_id
        JOIN Products  p ON p.product_id = i.product_id
        WHERE ci.cart_id = {cart_id}
        ORDER BY ci.cart_item_id
    """)

    validated = []
    subtotal = 0.0

    for r in rows:
        cart_item_id, requested_qty, inventory_id, seller_id, product_id, current_price, available_qty, product_name, image = r
        requested_qty = int(requested_qty)
        available_qty = int(available_qty)
        current_price = float(current_price)

        base = {
            "cart_item_id": cart_item_id,
            "inventory_id": inventory_id,
            "seller_id": seller_id,
            "product_id": product_id,
            "product_name": product_name,
            "image": image,
            "requested_qty": requested_qty,
            "available_qty": available_qty,
            "current_price": current_price,
        }

        if requested_qty <= available_qty and requested_qty > 0:
            line_total = current_price * requested_qty
            subtotal += line_total
            validated.append({
                **base,
                "ok": True,
                "line_total": line_total
            })
        else:
            # insufficient (or zero/negative) quantity requested
            validated.append({
                **base,
                "ok": False,
                "error": f"Only {available_qty} in stock" if available_qty >= 0 else "Not available",
                "line_total": 0.0
            })

    return validated, subtotal

@bp.route("/checkout", methods=["GET"])
@login_required
def checkout_page():
    cart_id = Cart.ensure_for_user(current_user.id)
    validated, subtotal = _validate_cart_for_checkout(cart_id)

    # If any not-ok rows, send to a page that shows errors + “Fix in cart” link
    any_bad = any(not it["ok"] for it in validated)
    if any_bad:
        return render_template("checkout.html", items=validated, subtotal=subtotal)

    # Otherwise proceed to confirmation page
    return render_template("checkout.html", items=validated, subtotal=subtotal)

@bp.route("/checkout/place", methods=["POST"])
@login_required
def checkout_place():
    # (Your existing place-order code goes here; unchanged.)
    # This route will assume the same validator and refuse if any item is invalid.
    cart_id = Cart.ensure_for_user(current_user.id)
    items, subtotal = _validate_cart_for_checkout(cart_id)
    if any(not it["ok"] for it in items):
        return render_template("checkout.html", items=items, subtotal=subtotal)

    # Example of the rest (use your existing logic if you already implemented it):
    rows = current_app.db.execute(
        f"INSERT INTO Orders(user_id, total_price, status) VALUES ({current_user.id}, {subtotal}, 'Pending') RETURNING order_id"
    )
    order_id = rows[0][0]

    for it in items:
        # double-check inventory snapshot
        inv_rows = current_app.db.execute(f"SELECT price, quantity FROM Inventory WHERE inventory_id = {it['inventory_id']}")
        price_now, qty_now = inv_rows[0]
        qty_now = int(qty_now)
        buy_qty = min(it["requested_qty"], qty_now)

        current_app.db.execute(
            f"""INSERT INTO OrderItems(order_id, inventory_id, quantity_required, final_unit_price, individual_fulfillment)
                VALUES ({order_id}, {it['inventory_id']}, {buy_qty}, {float(price_now)}, 'Not Yet Fulfilled')"""
        )
        current_app.db.execute(
            f"UPDATE Inventory SET quantity = {qty_now - buy_qty} WHERE inventory_id = {it['inventory_id']}"
        )

    # clear cart and redirect to order detail
    current_app.db.execute(f"DELETE FROM CartItems WHERE cart_id = {cart_id}")
    return redirect(url_for("orders.order_detail", order_id=order_id))