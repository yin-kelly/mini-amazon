# app/reviews.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from flask import current_app as app
import os
from werkzeug.utils import secure_filename

# Aggregated "recent reviews" model (your milestone helper)
from app.models.review import Review
from app.models.messaging import ReviewUpvote, ReviewImage
from app.models.social import Notification

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
        result = app.db.execute(
            """
            INSERT INTO ProductReviews (product_id, user_id, rating, feedback, created_at)
            VALUES (:pid, :uid, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
            ON CONFLICT (product_id, user_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                feedback = EXCLUDED.feedback,
                created_at = (current_timestamp AT TIME ZONE 'UTC')
            RETURNING review_id
            """,
            pid=product_id,
            uid=current_user.id,
            rating=rating,
            feedback=feedback,
        )
        
        # Handle image uploads
        if result and 'files' in request.files:
            review_id = result[0][0]
            files = request.files.getlist('files')
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        # Generate unique filename
                        import uuid
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(upload_dir, unique_filename)
                        
                        file.save(file_path)
                        
                        # Save image record
                        ReviewImage.create(
                            review_id=review_id,
                            review_type='product',
                            filename=unique_filename,
                            original_name=filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            mime_type=file.content_type or 'image/jpeg'
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
        result = app.db.execute(
            """
            INSERT INTO SellerReviews (seller_id, reviewer_id, rating, feedback, created_at)
            VALUES (:sid, :uid, :rating, :feedback, (current_timestamp AT TIME ZONE 'UTC'))
            ON CONFLICT (reviewer_id, seller_id)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                feedback = EXCLUDED.feedback,
                created_at = (current_timestamp AT TIME ZONE 'UTC')
            RETURNING review_id
            """,
            sid=seller_id,
            uid=current_user.id,
            rating=rating,
            feedback=feedback,
        )
        
        # Handle image uploads
        if result and 'files' in request.files:
            review_id = result[0][0]
            files = request.files.getlist('files')
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews')
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        # Generate unique filename
                        import uuid
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(upload_dir, unique_filename)
                        
                        file.save(file_path)
                        
                        # Save image record
                        ReviewImage.create(
                            review_id=review_id,
                            review_type='seller',
                            filename=unique_filename,
                            original_name=filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            mime_type=file.content_type or 'image/jpeg'
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


@bp.route("/reviews/product/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product_review(product_id: int):
    """Delete a product review by the current user"""
    app.db.execute(
        """
        DELETE FROM ProductReviews 
        WHERE product_id = :pid AND user_id = :uid
        """,
        pid=product_id,
        uid=current_user.id,
    )
    flash("Your product review was deleted.", "success")
    return redirect(url_for("reviews.my_reviews"))


@bp.route("/reviews/seller/<int:seller_id>/delete", methods=["POST"])
@login_required
def delete_seller_review(seller_id: int):
    """Delete a seller review by the current user"""
    app.db.execute(
        """
        DELETE FROM SellerReviews 
        WHERE seller_id = :sid AND reviewer_id = :uid
        """,
        sid=seller_id,
        uid=current_user.id,
    )
    flash("Your seller review was deleted.", "success")
    return redirect(url_for("reviews.my_reviews"))


@bp.route("/reviews/<review_type>/<int:review_id>/upvote", methods=["POST"])
@login_required
def toggle_upvote(review_type, review_id):
    """Toggle upvote for a review"""
    if review_type not in ['product', 'seller']:
        flash("Invalid review type.", "error")
        return redirect(request.referrer or url_for('index.index'))
    
    # Verify review exists
    if review_type == 'product':
        review_exists = app.db.execute('''
            SELECT 1 FROM ProductReviews WHERE review_id = :review_id
        ''', review_id=review_id)
    else:
        review_exists = app.db.execute('''
            SELECT 1 FROM SellerReviews WHERE review_id = :review_id
        ''', review_id=review_id)
    
    if not review_exists:
        flash("Review not found.", "error")
        return redirect(request.referrer or url_for('index.index'))
    
    # Toggle upvote
    is_upvoted = ReviewUpvote.toggle_upvote(review_id, review_type, current_user.id)
    
    if is_upvoted:
        # Get review author info for notification
        if review_type == 'product':
            review_info = app.db.execute('''
                SELECT pr.user_id, pr.feedback, p.name
                FROM ProductReviews pr
                JOIN Products p ON p.product_id = pr.product_id
                WHERE pr.review_id = :review_id
            ''', review_id=review_id)
        else:
            review_info = app.db.execute('''
                SELECT sr.reviewer_id, sr.feedback, u.firstname || ' ' || u.lastname as seller_name
                FROM SellerReviews sr
                JOIN Users u ON u.id = sr.seller_id
                WHERE sr.review_id = :review_id
            ''', review_id=review_id)
        
        if review_info:
            review_data = review_info[0]
            review_author_id = review_data[0]
            review_content = review_data[1]
            target_name = review_data[2]
            
            # Create notification for review author
            Notification.create(review_author_id, 'upvote', {
                'review_id': review_id,
                'review_type': review_type,
                'review_content': review_content[:100] + '...' if len(review_content) > 100 else review_content,
                'target_name': target_name,
                'upvoter_name': f"{current_user.firstname} {current_user.lastname}"
            })
        
        flash("Review upvoted!", "success")
    else:
        flash("Upvote removed.", "info")
    
    return redirect(request.referrer or url_for('index.index'))


@bp.route("/reviews/images/<int:image_id>")
def view_image(image_id):
    """Serve review images"""
    from flask import send_file
    
    image_info = app.db.execute('''
        SELECT file_path, mime_type FROM ReviewImages WHERE image_id = :image_id
    ''', image_id=image_id)
    
    if not image_info:
        flash("Image not found.", "error")
        return redirect(url_for('index.index'))
    
    file_path = image_info[0][0]
    mime_type = image_info[0][1]
    
    if os.path.exists(file_path):
        return send_file(file_path, mimetype=mime_type)
    else:
        flash("Image file not found.", "error")
        return redirect(url_for('index.index'))
