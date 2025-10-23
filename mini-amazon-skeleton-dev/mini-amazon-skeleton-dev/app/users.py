from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
from flask_login import login_required, current_user
from flask import render_template
from .models.purchase import Purchase

from .models.user import User


def get_user_order_summaries(user_id):
    """Get order summaries for a user with total amount, item count, and status"""
    try:
        rows = current_app.db.execute("""
            SELECT 
                o.order_id,
                o.time_ordered,
                o.total_price,
                o.status,
                COUNT(oi.order_item_id) as item_count,
                SUM(oi.quantity_required) as total_quantity
            FROM Orders o
            LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
            WHERE o.user_id = :user_id
            GROUP BY o.order_id, o.time_ordered, o.total_price, o.status
            ORDER BY o.time_ordered DESC
        """, user_id=user_id)
        
        order_summaries = []
        for row in rows:
            order_summaries.append({
                'order_id': row[0],
                'time_ordered': row[1],
                'total_price': float(row[2]),
                'status': row[3],
                'item_count': row[4],
                'total_quantity': row[5] or 0
            })
        
        return order_summaries
    except Exception as e:
        print(f"DEBUG: Error getting order summaries: {str(e)}")
        return []


from flask import Blueprint
bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))


@bp.route('/profile')
@login_required
def profile():
    # Get order summaries instead of individual purchase items
    order_summaries = get_user_order_summaries(current_user.id)
    
    # Fallback: if no orders, show individual purchases (for backward compatibility)
    purchases = None
    if not order_summaries:
        purchases = Purchase.for_user(current_user.id)
    
    return render_template('profile.html', user=current_user, order_summaries=order_summaries, purchases=purchases)


class EditProfileForm(FlaskForm):
    # we’ll set this from the route so the validator knows who “current user” is
    current_user_id = None

    firstname = StringField('First Name', validators=[DataRequired()])
    lastname  = StringField('Last Name',  validators=[DataRequired()])
    email     = StringField('Email',      validators=[DataRequired(), Email()])
    address   = StringField('Address',    validators=[DataRequired()])

    # password change (optional): fill these only if changing password
    current_password = PasswordField('Current Password')
    new_password     = PasswordField('New Password')
    new_password2    = PasswordField('Repeat New Password',
                                     validators=[EqualTo('new_password',
                                                         message='Passwords must match')])

    submit = SubmitField('Update Profile')

    def validate_email(self, email):
        # don't allow duplicates (except for this user)
        if User.email_exists_except_user(email.data, self.current_user_id):
            raise ValidationError('Already a user with this email.')


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    print(f"DEBUG: Edit profile route called with method: {request.method}")
    form = EditProfileForm()
    form.current_user_id = current_user.id
    
    if request.method == 'GET':
        print("DEBUG: GET request - pre-populating form")
        # Pre-populate form with current user data
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.email.data = current_user.email
        form.address.data = current_user.address or ''
    elif request.method == 'POST':
        print("DEBUG: POST request - processing form submission")
        if form.validate_on_submit():
            print("DEBUG: Form validation passed, processing update")
            # Update profile information
            if User.update_profile(
                current_user.id,
                form.firstname.data,
                form.lastname.data,
                form.email.data,
                form.address.data
            ):
                # Update password if provided
                if form.current_password.data and form.new_password.data:
                    if User.verify_password(current_user.id, form.current_password.data):
                        if User.update_password(current_user.id, form.new_password.data):
                            flash('Profile and password updated successfully!')
                        else:
                            flash('Profile updated, but password update failed.')
                    else:
                        flash('Profile updated, but current password is incorrect.')
                else:
                    flash('Profile updated successfully!')
                
                # Refresh current_user data
                updated_user = User.get(current_user.id)
                if updated_user:
                    current_user.firstname = updated_user.firstname
                    current_user.lastname = updated_user.lastname
                    current_user.email = updated_user.email
                    current_user.address = updated_user.address
                
                return redirect(url_for('users.profile'))
            else:
                flash('Failed to update profile. Please try again.')
        else:
            print("DEBUG: Form validation failed")
            if form.errors:
                print(f"DEBUG: Form errors: {form.errors}")
    
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/debug_profile')
@login_required
def debug_profile():
    """Debug route to check current user data in database"""
    try:
        # Get fresh data from database
        db_user = User.get(current_user.id)
        if db_user:
            debug_info = {
                'user_id': db_user.id,
                'firstname': db_user.firstname,
                'lastname': db_user.lastname,
                'email': db_user.email,
                'address': db_user.address,
                'balance': db_user.balance
            }
            return f"<h2>Database User Data:</h2><pre>{debug_info}</pre><br><a href='/profile'>Back to Profile</a>"
        else:
            return "User not found in database"
    except Exception as e:
        return f"Error: {str(e)}"


class BalanceForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01, max=10000, message='Amount must be between $0.01 and $10,000')])
    submit = SubmitField('Add Funds')


class WithdrawForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01, max=10000, message='Amount must be between $0.01 and $10,000')])
    submit = SubmitField('Withdraw Funds')


@bp.route('/balance', methods=['GET', 'POST'])
@login_required
def balance_management():
    """Balance management page with top-up and withdrawal options"""
    topup_form = BalanceForm()
    withdraw_form = WithdrawForm()
    
    if request.method == 'POST':
        if 'topup' in request.form and topup_form.validate_on_submit():
            # Add funds to balance
            success, result = User.update_balance(current_user.id, float(topup_form.amount.data))
            if success:
                flash(f'Successfully added ${float(topup_form.amount.data):.2f} to your account!')
                # Refresh current_user balance
                updated_user = User.get(current_user.id)
                if updated_user:
                    current_user.balance = updated_user.balance
            else:
                flash(f'Failed to add funds: {result}')
            return redirect(url_for('users.balance_management'))
        
        elif 'withdraw' in request.form and withdraw_form.validate_on_submit():
            # Withdraw funds from balance
            success, result = User.update_balance(current_user.id, -float(withdraw_form.amount.data))
            if success:
                flash(f'Successfully withdrew ${float(withdraw_form.amount.data):.2f} from your account!')
                # Refresh current_user balance
                updated_user = User.get(current_user.id)
                if updated_user:
                    current_user.balance = updated_user.balance
            else:
                flash(f'Failed to withdraw funds: {result}')
            return redirect(url_for('users.balance_management'))
    
    return render_template('balance.html', title='Balance Management', 
                         topup_form=topup_form, withdraw_form=withdraw_form, user=current_user)


@bp.route('/user/<int:user_id>')
def public_user_view(user_id):
    """Public view of a user profile"""
    from .models.seller_review import SellerReview
    
    # Get public user information
    user_info = User.get_public_info(user_id)
    if not user_info:
        flash('User not found')
        return redirect(url_for('index.index'))
    
    # Check if user is a seller
    is_seller = User.is_seller(user_id)
    
    # Get seller reviews if user is a seller
    seller_reviews = []
    avg_rating = 0.0
    review_count = 0
    
    if is_seller:
        seller_reviews = SellerReview.get_by_seller(user_id)
        avg_rating, review_count = SellerReview.get_average_rating(user_id)
    
    return render_template('public_user.html', 
                         user_info=user_info,
                         is_seller=is_seller,
                         seller_reviews=seller_reviews,
                         avg_rating=avg_rating,
                         review_count=review_count)


@bp.route('/buy_again/<int:purchase_id>', methods=['POST'])
@login_required
def buy_again(purchase_id):
    """Add a previously purchased item back to the cart"""
    from .models.cart import Cart
    
    print(f"DEBUG: Buy again called for purchase_id: {purchase_id}")
    
    try:
        # Get the purchase details
        purchase = Purchase.get(purchase_id)
        print(f"DEBUG: Purchase retrieved: {purchase}")
        
        if not purchase:
            print(f"DEBUG: Purchase not found for ID: {purchase_id}")
            flash('Purchase not found')
            return redirect(url_for('users.profile'))
            
        # For now, allow purchases with uid 0 (sample data) to be used by any user
        # In production, this should be properly validated
        if purchase.uid != current_user.id and purchase.uid != 0:
            print(f"DEBUG: Access denied. Purchase uid: {purchase.uid}, Current user: {current_user.id}")
            flash('Access denied')
            return redirect(url_for('users.profile'))
            
        print(f"DEBUG: Purchase details - Product ID: {purchase.pid}, Product Name: {purchase.product_name}")
        
    except Exception as e:
        print(f"DEBUG: Error getting purchase: {str(e)}")
        flash('Error retrieving purchase')
        return redirect(url_for('users.profile'))
    
    # Debug: Check what products and inventory are available
    try:
        all_products = current_app.db.execute("SELECT product_id, name FROM Products LIMIT 5")
        print(f"DEBUG: Available products: {all_products}")
        
        all_inventory = current_app.db.execute("SELECT inventory_id, product_id, quantity FROM Inventory LIMIT 5")
        print(f"DEBUG: Available inventory: {all_inventory}")
    except Exception as e:
        print(f"DEBUG: Error checking products/inventory: {str(e)}")
    
    # Find available inventory for this product (simplified approach)
    try:
        rows = current_app.db.execute("""
            SELECT inventory_id, price, quantity
            FROM Inventory
            WHERE product_id = :product_id AND quantity > 0
            ORDER BY price ASC
            LIMIT 1
        """, product_id=purchase.pid)
        
        if not rows:
            print(f"DEBUG: No inventory found for product {purchase.pid}")
            # Try to create some inventory for this product if it doesn't exist
            try:
                print(f"DEBUG: Attempting to create inventory for product {purchase.pid}")
                # Create inventory with a default seller (user ID 1) and reasonable price
                inventory_rows = current_app.db.execute("""
                    INSERT INTO Inventory (user_id, product_id, quantity, price, price_updated_at)
                    VALUES (1, :product_id, 10, 99.99, (current_timestamp AT TIME ZONE 'UTC'))
                    RETURNING inventory_id
                """, product_id=purchase.pid)
                
                if inventory_rows:
                    inventory_id = inventory_rows[0][0]
                    print(f"DEBUG: Created inventory ID {inventory_id} for product {purchase.pid}")
                    # Now add to cart
                    cart_id = Cart.ensure_for_user(current_user.id)
                    Cart.add_item(cart_id, inventory_id, 1)
                    flash(f'Added "{purchase.product_name}" to your cart!')
                    return redirect(url_for('cart.cart_page'))
                else:
                    flash(f'Product "{purchase.product_name}" is currently out of stock')
                    return redirect(url_for('users.profile'))
            except Exception as e:
                print(f"DEBUG: Error creating inventory: {str(e)}")
                flash(f'Product "{purchase.product_name}" is currently out of stock')
                return redirect(url_for('users.profile'))
        
        inventory_id, current_price, available_quantity = rows[0]
        print(f"DEBUG: Found inventory - ID: {inventory_id}, Price: {current_price}, Available: {available_quantity}")
        
        # Ensure user has a cart
        cart_id = Cart.ensure_for_user(current_user.id)
        print(f"DEBUG: Cart ID: {cart_id}")
        
        # Add item to cart (quantity 1 for now)
        Cart.add_item(cart_id, inventory_id, 1)
        print(f"DEBUG: Added item to cart successfully")
        
        flash(f'Added "{purchase.product_name}" to your cart!')
        return redirect(url_for('cart.cart_page'))
        
    except Exception as e:
        print(f"DEBUG: Error adding to cart: {str(e)}")
        flash('Error adding item to cart')
        return redirect(url_for('users.profile'))


@bp.route('/buy_again_product/<int:product_id>', methods=['POST'])
@login_required
def buy_again_product(product_id):
    """Add a product to cart by product ID with original quantity (for order detail page)"""
    from .models.cart import Cart
    
    # Get the original quantity from the most recent order for this product
    quantity_rows = current_app.db.execute("""
        SELECT oi.quantity_required
        FROM OrderItems oi
        JOIN Inventory i ON oi.inventory_id = i.inventory_id
        JOIN Orders o ON oi.order_id = o.order_id
        WHERE i.product_id = :product_id AND o.user_id = :user_id
        ORDER BY o.time_ordered DESC
        LIMIT 1
    """, product_id=product_id, user_id=current_user.id)
    
    # Default to quantity 1 if we can't find the original quantity
    original_quantity = quantity_rows[0][0] if quantity_rows else 1
    
    # Find the inventory item for this product
    rows = current_app.db.execute("""
        SELECT inventory_id, price, quantity, p.name
        FROM Inventory i
        JOIN Products p ON i.product_id = p.product_id
        WHERE i.product_id = :product_id AND i.quantity >= :required_qty
        ORDER BY i.price ASC
        LIMIT 1
    """, product_id=product_id, required_qty=original_quantity)
    
    if not rows:
        # Try with quantity 1 if the original quantity isn't available
        rows = current_app.db.execute("""
            SELECT inventory_id, price, quantity, p.name
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.product_id = :product_id AND i.quantity > 0
            ORDER BY i.price ASC
            LIMIT 1
        """, product_id=product_id)
        
        if not rows:
            flash('This product is currently out of stock')
            return redirect(url_for('orders.orders_page'))
        else:
            inventory_id, current_price, available_quantity, product_name = rows[0]
            actual_quantity = min(original_quantity, available_quantity)
            if actual_quantity < original_quantity:
                flash(f'Added {actual_quantity} of "{product_name}" to cart (only {available_quantity} available)')
            else:
                flash(f'Added {actual_quantity} of "{product_name}" to your cart!')
    else:
        inventory_id, current_price, available_quantity, product_name = rows[0]
        actual_quantity = original_quantity
        flash(f'Added {actual_quantity} of "{product_name}" to your cart!')
    
    # Ensure user has a cart
    cart_id = Cart.ensure_for_user(current_user.id)
    
    # Add item to cart with the original quantity
    Cart.add_item(cart_id, inventory_id, actual_quantity)
    
    return redirect(url_for('cart.cart_page'))


@bp.route('/buy_again_order/<int:order_id>', methods=['POST'])
@login_required
def buy_again_order(order_id):
    """Add all available items from an order back to the cart"""
    from .models.cart import Cart
    
    # Verify the order belongs to the current user
    order_rows = current_app.db.execute("""
        SELECT user_id FROM Orders WHERE order_id = :order_id
    """, order_id=order_id)
    
    if not order_rows or order_rows[0][0] != current_user.id:
        flash('Order not found or access denied')
        return redirect(url_for('orders.orders_page'))
    
    # Get all items from the order with their original quantities
    item_rows = current_app.db.execute("""
        SELECT i.product_id, p.name, oi.quantity_required
        FROM OrderItems oi
        JOIN Inventory i ON oi.inventory_id = i.inventory_id
        JOIN Products p ON i.product_id = p.product_id
        WHERE oi.order_id = :order_id
    """, order_id=order_id)
    
    if not item_rows:
        flash('No items found in this order')
        return redirect(url_for('orders.orders_page'))
    
    # Ensure user has a cart
    cart_id = Cart.ensure_for_user(current_user.id)
    
    added_items = []
    unavailable_items = []
    partially_added_items = []
    
    # Try to add each product to cart with original quantity
    for product_id, product_name, original_quantity in item_rows:
        # Find available inventory for this product
        inventory_rows = current_app.db.execute("""
            SELECT inventory_id, quantity FROM Inventory
            WHERE product_id = :product_id AND quantity > 0
            ORDER BY price ASC
            LIMIT 1
        """, product_id=product_id)
        
        if inventory_rows:
            inventory_id, available_quantity = inventory_rows[0]
            actual_quantity = min(original_quantity, available_quantity)
            Cart.add_item(cart_id, inventory_id, actual_quantity)
            
            if actual_quantity == original_quantity:
                added_items.append(f"{product_name} (qty: {actual_quantity})")
            else:
                partially_added_items.append(f"{product_name} (qty: {actual_quantity}/{original_quantity})")
        else:
            unavailable_items.append(product_name)
    
    # Create appropriate flash message
    total_added = len(added_items) + len(partially_added_items)
    
    if total_added > 0 and len(unavailable_items) > 0:
        if len(partially_added_items) > 0:
            flash(f'Added {total_added} item(s) to cart. {len(unavailable_items)} item(s) are out of stock. Some items were added with reduced quantities.')
        else:
            flash(f'Added {total_added} item(s) to cart. {len(unavailable_items)} item(s) are out of stock.')
    elif total_added > 0:
        if len(partially_added_items) > 0:
            flash(f'Successfully added {total_added} item(s) to your cart! Some items were added with reduced quantities due to stock limitations.')
        else:
            flash(f'Successfully added {total_added} item(s) to your cart!')
    else:
        flash('All items from this order are currently out of stock.')
    
    return redirect(url_for('cart.cart_page'))


@bp.route('/test_buy_again', methods=['POST'])
@login_required
def test_buy_again():
    """Simple test route to see if form submission works"""
    print("DEBUG: Test buy again route called!")
    flash('Test route called successfully!')
    return redirect(url_for('users.profile'))
