# app/messaging.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .models.messaging import MessageThread, Message
from .models.social import Notification

bp = Blueprint('messaging', __name__, url_prefix='/messages')

@bp.route('')
@login_required
def index():
    """Show all message threads for the current user"""
    threads = MessageThread.get_by_user(current_user.id)
    return render_template('messages/index.html', threads=threads)

@bp.route('/thread/<int:thread_id>')
@login_required
def view_thread(thread_id):
    """View a specific message thread"""
    # Get thread info
    thread_info = current_app.db.execute('''
        SELECT mt.thread_id, mt.order_id, mt.buyer_id, mt.seller_id, mt.created_at,
               o.time_ordered, o.status,
               buyer.firstname || ' ' || buyer.lastname as buyer_name,
               seller.firstname || ' ' || seller.lastname as seller_name
        FROM MessageThreads mt
        JOIN Orders o ON o.order_id = mt.order_id
        JOIN Users buyer ON buyer.id = mt.buyer_id
        JOIN Users seller ON seller.id = mt.seller_id
        WHERE mt.thread_id = :thread_id AND (mt.buyer_id = :user_id OR mt.seller_id = :user_id)
    ''', thread_id=thread_id, user_id=current_user.id)
    
    if not thread_info:
        flash('Message thread not found or access denied.', 'error')
        return redirect(url_for('messaging.index'))
    
    thread_data = thread_info[0]
    thread = MessageThread(*thread_data[:5])
    thread.order_date = thread_data[5]
    thread.order_status = thread_data[6]
    thread.buyer_name = thread_data[7]
    thread.seller_name = thread_data[8]
    
    # Get messages
    messages = Message.get_by_thread(thread_id)
    
    return render_template('messages/thread.html', thread=thread, messages=messages)

@bp.route('/thread/<int:thread_id>/send', methods=['POST'])
@login_required
def send_message(thread_id):
    """Send a message in a thread"""
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message content cannot be empty.', 'error')
        return redirect(url_for('messaging.view_thread', thread_id=thread_id))
    
    # Verify user has access to this thread
    thread_info = current_app.db.execute('''
        SELECT buyer_id, seller_id FROM MessageThreads
        WHERE thread_id = :thread_id AND (buyer_id = :user_id OR seller_id = :user_id)
    ''', thread_id=thread_id, user_id=current_user.id)
    
    if not thread_info:
        flash('Access denied.', 'error')
        return redirect(url_for('messaging.index'))
    
    # Create message
    Message.create(thread_id, current_user.id, content)
    
    # Get thread info for notification
    thread_info = current_app.db.execute('''
        SELECT buyer_id, seller_id FROM MessageThreads WHERE thread_id = :thread_id
    ''', thread_id=thread_id)
    
    if thread_info:
        buyer_id, seller_id = thread_info[0]
        # Notify the other party
        other_user_id = seller_id if current_user.id == buyer_id else buyer_id
        
        Notification.create(other_user_id, 'message', {
            'thread_id': thread_id,
            'sender_name': f"{current_user.firstname} {current_user.lastname}",
            'message_preview': content[:100] + '...' if len(content) > 100 else content
        })
    
    flash('Message sent successfully.', 'success')
    
    return redirect(url_for('messaging.view_thread', thread_id=thread_id))

@bp.route('/start/<int:order_id>/<int:seller_id>', methods=['POST'])
@login_required
def start_thread(order_id, seller_id):
    """Start a new message thread for an order and seller"""
    # Verify the user is the buyer of this order
    order_info = current_app.db.execute('''
        SELECT user_id FROM Orders WHERE order_id = :order_id
    ''', order_id=order_id)
    
    if not order_info or order_info[0][0] != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.orders_page'))
    
    # Check if thread already exists
    existing_thread = MessageThread.get_by_order_and_seller(order_id, seller_id)
    
    if existing_thread:
        return redirect(url_for('messaging.view_thread', thread_id=existing_thread.id))
    
    # Create new thread
    thread_id = MessageThread.create(order_id, current_user.id, seller_id)
    
    if thread_id:
        flash('Message thread started.', 'success')
        return redirect(url_for('messaging.view_thread', thread_id=thread_id))
    else:
        flash('Failed to create message thread.', 'error')
        return redirect(url_for('orders.orders_page'))
