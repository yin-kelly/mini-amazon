# app/notifications.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from .models.social import Notification

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@bp.route('')
@login_required
def index():
    """View all notifications"""
    notifications = Notification.get_for_user(current_user.id)
    return render_template('notifications/index.html', notifications=notifications)

@bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread notification count (for AJAX)"""
    count = Notification.get_unread_count(current_user.id)
    return jsonify({'count': count})

@bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read"""
    Notification.mark_read(notification_id, current_user.id)
    return jsonify({'success': True})

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    Notification.mark_all_read(current_user.id)
    return jsonify({'success': True})
