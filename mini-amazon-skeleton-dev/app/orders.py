# app/orders.py
from flask import Blueprint, render_template, current_app, abort
from flask_login import login_required, current_user

bp = Blueprint("orders", __name__)

@bp.route("/orders")
@login_required
def orders_page():
    uid = int(current_user.id)
    rows = current_app.db.execute(
        f"""
        SELECT order_id, time_ordered, total_price, status
        FROM Orders
        WHERE user_id = {uid}
        ORDER BY time_ordered DESC
        """
    )
    orders = [
        {
            "order_id": r[0],
            "time_ordered": r[1],
            "total_price": float(r[2]),
            "status": r[3],
        }
        for r in rows
    ]
    return render_template("orders.html", orders=orders)

@bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id: int):
    oid = int(order_id)

    # header
    hdr_rows = current_app.db.execute(
        f"""
        SELECT order_id, user_id, time_ordered, total_price, status
        FROM Orders
        WHERE order_id = {oid}
        """
    )
    if not hdr_rows:
        abort(404)

    order_id_, uid, time_ordered, total_price, status = hdr_rows[0]
    if int(uid) != int(current_user.id):
        abort(403)

    # items
    item_rows = current_app.db.execute(
        f"""
        SELECT
            oi.order_item_id,
            p.product_id,
            p.name,
            i.user_id       AS seller_id,
            oi.quantity_required,
            oi.final_unit_price,
            oi.individual_fulfillment
        FROM OrderItems oi
        JOIN Inventory i ON i.inventory_id = oi.inventory_id
        JOIN Products  p ON p.product_id = i.product_id
        WHERE oi.order_id = {oid}
        ORDER BY oi.order_item_id
        """
    )

    items = []
    subtotal = 0.0
    for r in item_rows:
        order_item_id, product_id, product_name, seller_id, qty, unit_price, item_status = r
        qty = int(qty)
        unit_price = float(unit_price)
        line_total = unit_price * qty
        subtotal += line_total
        items.append({
            "order_item_id": order_item_id,
            "product_id": product_id,
            "product_name": product_name,
            "seller_id": seller_id,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "item_status": item_status or status,  # fallback
        })

    return render_template(
        "order_detail.html",
        order={
            "order_id": order_id_,
            "time_ordered": time_ordered,
            "total_price": float(total_price),
            "status": status,
        },
        items=items,
        subtotal=subtotal
    )