"""
Notification Service — business logic for sending and managing notifications.
"""

from models.notification import (
    create_notification,
    get_notifications_for_user,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
)


def notify_user(user_id, message, notif_type='Info'):
    """
    Send a notification to a specific user.

    Parameters
    ----------
    user_id : str
    message : str
    notif_type : str — 'Info', 'Warning', 'Success', 'Error'
    """
    return create_notification(user_id, message, notif_type)


def notify_attendance_marked(user_id, username, result):
    """Send an attendance-related notification to the user."""
    if result == 'check-in':
        msg = f"Welcome, {username}! Your check-in has been recorded."
        return create_notification(user_id, msg, 'Success')
    elif result == 'check-out':
        msg = f"Goodbye, {username}! Your check-out has been recorded."
        return create_notification(user_id, msg, 'Success')
    elif result == 'time_restricted_in':
        msg = f"Check-in rejected for {username}: allowed only 10-11 AM."
        return create_notification(user_id, msg, 'Warning')
    elif result == 'time_restricted_out':
        msg = f"Check-out rejected for {username}: allowed only 4-5 PM."
        return create_notification(user_id, msg, 'Warning')


def notify_account_created(user_id, username):
    """Notify a new user that their account has been created."""
    msg = f"Welcome, {username}! Your account has been created. Default password is 'changeme'."
    return create_notification(user_id, msg, 'Info')


def get_user_notifications(user_id, unread_only=False):
    """Fetch notifications for the current user."""
    return get_notifications_for_user(user_id, unread_only=unread_only)


def get_user_unread_count(user_id):
    """Return unread notification count."""
    return get_unread_count(user_id)


def read_notification(notif_id):
    """Mark a notification as read."""
    mark_as_read(notif_id)


def read_all_notifications(user_id):
    """Mark all notifications for a user as read."""
    mark_all_as_read(user_id)
