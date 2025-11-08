# app/orders.py
from flask import Blueprint, render_template, current_app, abort, request
from flask_login import login_required, current_user

bp = Blueprint("orders", __name__)

@bp.route("/orders")
@login_required
def orders_page():
    uid = int(current_user.id)
    
    # Get search parameters
    search_item = request.args.get('search_item', '').strip()
    search_seller = request.args.get('search_seller', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    
    # Build the base query
    base_query = """
        SELECT 
            o.order_id,
            o.time_ordered,
            o.total_price,
            o.status,
            COUNT(oi.order_item_id) as item_count,
            SUM(oi.quantity_required) as total_quantity
        FROM Orders o
        LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
        LEFT JOIN Inventory i ON oi.inventory_id = i.inventory_id
        LEFT JOIN Products p ON i.product_id = p.product_id
        LEFT JOIN Users u ON i.user_id = u.id
        WHERE o.user_id = :user_id
    """
    
    # Add filters
    filters = []
    params = {'user_id': uid}
    
    if search_item:
        filters.append("LOWER(p.name) LIKE LOWER(:search_item)")
        params['search_item'] = f'%{search_item}%'
    
    if search_seller:
        filters.append("LOWER(u.firstname || ' ' || u.lastname) LIKE LOWER(:search_seller)")
        params['search_seller'] = f'%{search_seller}%'
    
    if date_from:
        filters.append("o.time_ordered >= :date_from")
        params['date_from'] = date_from
    
    if date_to:
        filters.append("o.time_ordered <= :date_to")
        params['date_to'] = date_to + ' 23:59:59'
    
    if status_filter:
        filters.append("o.status = :status_filter")
        params['status_filter'] = status_filter
    
    # Add filters to query
    if filters:
        base_query += " AND " + " AND ".join(filters)
    
    # Add GROUP BY and ORDER BY
    base_query += """
        GROUP BY o.order_id, o.time_ordered, o.total_price, o.status
        ORDER BY o.time_ordered DESC
    """
    
    rows = current_app.db.execute(base_query, **params)
    
    orders = []
    for row in rows:
        orders.append({
            'order_id': row[0],
            'time_ordered': row[1],
            'total_price': float(row[2]),
            'status': row[3],
            'item_count': row[4],
            'total_quantity': row[5] or 0
        })
    
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