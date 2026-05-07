"""
User routes blueprint — employee-facing features: profile, notifications, activity log.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for, jsonify

from models.db import get_db_connection
from models.notification import get_notifications_for_user, get_unread_count, mark_as_read, mark_all_as_read
from models.activity import get_activities_by_user
from models.attendance_summary import AttendanceSummary
from models.payroll import PayrollIntegration
from services.report_service import calculate_attendance_summary
from utils.decorators import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/notifications')
@login_required
def notifications():
    """Show notifications page for the logged-in user."""
    user_id = _get_user_id()
    if user_id is None:
        return redirect(url_for('auth.login'))

    notifs = get_notifications_for_user(user_id)
    unread = get_unread_count(user_id)
    return render_template('notifications.html', notifications=notifs, unread_count=unread)


@user_bp.route('/notifications/json')
@login_required
def notifications_json():
    """API endpoint: return notifications as JSON."""
    user_id = _get_user_id()
    if user_id is None:
        return jsonify(success=False, message="User not found"), 404

    unread_only = request.args.get('unread', 'false').lower() == 'true'
    notifs = get_notifications_for_user(user_id, unread_only=unread_only)
    unread = get_unread_count(user_id)

    return jsonify(
        success=True,
        unread_count=unread,
        notifications=[
            {
                'id': n['notifId'],
                'message': n['message'],
                'type': n['type'],
                'isRead': bool(n['isRead']),
                'sentAt': n['sentAt'].strftime('%Y-%m-%d %H:%M:%S') if n['sentAt'] else '',
            }
            for n in notifs
        ],
    )


@user_bp.route('/notifications/read/<notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark a single notification as read."""
    mark_as_read(notif_id)
    return jsonify(success=True)


@user_bp.route('/notifications/read_all', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications for the current user as read."""
    user_id = _get_user_id()
    if user_id:
        mark_all_as_read(user_id)
    return jsonify(success=True)


@user_bp.route('/activity')
@login_required
def activity_log():
    """Show the activity log for the logged-in user."""
    user_id = _get_user_id()
    if user_id is None:
        return redirect(url_for('auth.login'))

    activities = get_activities_by_user(user_id)
    return render_template('activity_log.html', activities=activities)


@user_bp.route('/activity/json')
@login_required
def activity_json():
    """API endpoint: return activity log as JSON."""
    user_id = _get_user_id()
    if user_id is None:
        return jsonify(success=False, message="User not found"), 404

    activities = get_activities_by_user(user_id)
    return jsonify(
        success=True,
        activities=[
            {
                'id': a['actId'],
                'action': a['action'],
                'location': a['location'],
                'timestamp': a['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if a['timestamp'] else '',
            }
            for a in activities
        ],
    )


@user_bp.route('/summary')
@login_required
def user_summary():
    """Show attendance summary and payroll estimate for the logged-in user."""
    user_id = _get_user_id()
    if user_id is None:
        return redirect(url_for('auth.login'))
        
    import datetime
    period = request.args.get('period', datetime.datetime.now().strftime('%Y-%m'))
    
    # Ensure current summary is calculated
    calculate_attendance_summary(user_id, period)
    
    summary = AttendanceSummary.get_by_user_and_period(user_id, period)
    payroll = PayrollIntegration.get_by_user_and_month(user_id, period)
    
    return render_template('user_summary.html', summary=summary, payroll=payroll, period=period)

# ─── Helpers ────────────────────────────────────────────

def _get_user_id():
    """Look up the current session user's numeric ID from the legacy users table."""
    username = session.get('user')
    if not username:
        return None
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return str(row['id']) if row else None
