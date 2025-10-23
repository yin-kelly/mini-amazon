# app/reviews.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from flask import current_app as app

# Aggregated "recent reviews" model (your milestone helper)
from app.models.review import Review

bp = Blueprint("reviews", __name__)

@bp.route("/my/reviews")
@login_required
def my_reviews():
    limit = int(request.args.get("limit", 5))
    kind = request.args.get("type")  # 'product' | 'seller' | None
    sort = request.args.get("sort", "date")  # 'date' | 'rating'
    items = Review.get_recent_by_user(current_user.id, limit=limit, kind=kind, sort=sort)
    return render_template("my_reviews.html", reviews=items, kind=kind, sort=sort)

@bp.route("/users/<int:uid>/reviews")
def user_reviews(uid):
    limit = int(request.args.get("limit", 5))
    kind = request.args.get("type")
    sort = request.args.get("sort", "date")
    items = Review.get_recent_by_user(uid, limit=limit, kind=kind, sort=sort)
    return render_template("my_reviews.html", reviews=items, kind=kind, sort=sort, viewing_uid=uid)

# Create/Edit a PRODUCT review
@bp.route("/reviews/product/<int:product_id>/new", methods=["GET", "POST"])
@login_required
def new_product_review(product_id: int):
    """
    Only allow reviewing a product if the current user has purchased it.
    OrderItems doesn't carry product_id directly; we must join through Inventory.
    """
    bought = app.db.execute(
        """
        SELECT 1
        FROM Orders o
        JOIN OrderItems oi ON oi.order_id = o.order_id
        JOIN Inventory inv ON inv.inventory_id = oi.inventory_id
        WHERE o.user_id = :uid
          AND inv.product_id = :pid
        LIMIT 1
        """,
        uid=current_user.id,
        pid=product_id,
    )

    if not bought:
        flash("You can only review products you have purchased.", "warning")
        return redirect(url_for("orders.orders_page"))

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", "0"))
        except ValueError:
            rating = 0
        feedback = (request.form.get("feedback") or "").strip() or None

        # Upsert: create new or update existing (unique on (product_id, user_id))
        app.db.execute(
            """
            INSERT INTO ProductReviews (product_id, user_id, rating, feedback, created_at)
            VALUES (:pid, :uid, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
            ON CONFLICT (product_id, user_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                feedback = EXCLUDED.feedback,
                created_at = (current_timestamp AT TIME ZONE 'UTC')
            """,
            pid=product_id,
            uid=current_user.id,
            rating=rating,
            feedback=feedback,
        )
        flash("Your product review was saved.", "success")
        return redirect(url_for("reviews.my_reviews"))

    # GET prefill existing values if any
    existing = app.db.execute(
        """
        SELECT rating, feedback
        FROM ProductReviews
        WHERE product_id = :pid AND user_id = :uid
        """,
        pid=product_id,
        uid=current_user.id,
    )
    rating = existing[0][0] if existing else ""
    feedback = existing[0][1] if existing else ""
    return render_template(
        "review_form.html",
        mode="product",
        product_id=product_id,
        rating=rating,
        feedback=feedback,
        title="Review Product",
        submit_label="Save Product Review",
    )


# Create/Edit a SELLER review
@bp.route("/reviews/seller/<int:seller_id>/new", methods=["GET", "POST"])
@login_required
def new_seller_review(seller_id: int):
    """
    Only allow reviewing a seller if the current user placed an order
    containing items from that seller (seller lives on Inventory.user_id).
    """
    purchased_from_seller = app.db.execute(
        """
        SELECT 1
        FROM Orders o
        JOIN OrderItems oi ON oi.order_id = o.order_id
        JOIN Inventory inv ON inv.inventory_id = oi.inventory_id
        WHERE o.user_id = :uid
          AND inv.user_id = :sid
        LIMIT 1
        """,
        uid=current_user.id,
        sid=seller_id,
    )

    if not purchased_from_seller:
        flash("You can only review sellers you have bought from.", "warning")
        return redirect(url_for("orders.orders_page"))

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", "0"))
        except ValueError:
            rating = 0
        feedback = (request.form.get("feedback") or "").strip() or None

        # Upsert: one review per (reviewer_id, seller_id)
        app.db.execute(
            """
            INSERT INTO SellerReviews (seller_id, reviewer_id, rating, feedback, created_at)
            VALUES (:sid, :uid, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
            ON CONFLICT (reviewer_id, seller_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                feedback = EXCLUDED.feedback,
                created_at = (current_timestamp AT TIME ZONE 'UTC')
            """,
            sid=seller_id,
            uid=current_user.id,
            rating=rating,
            feedback=feedback,
        )
        flash("Your seller review was saved.", "success")
        return redirect(url_for("reviews.my_reviews"))

    # GET prefill existing values if any
    existing = app.db.execute(
        """
        SELECT rating, feedback
        FROM SellerReviews
        WHERE seller_id = :sid AND reviewer_id = :uid
        """,
        sid=seller_id,
        uid=current_user.id,
    )
    rating = existing[0][0] if existing else ""
    feedback = existing[0][1] if existing else ""
    return render_template(
        "review_form.html",
        mode="seller",
        seller_id=seller_id,
        rating=rating,
        feedback=feedback,
        title="Review Seller",
        submit_label="Save Seller Review",
    )
