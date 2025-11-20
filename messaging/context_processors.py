def messaging_counts(request):
    """Expose unread messages count and pending friend requests for navbar badges if authenticated."""
    if not request.user.is_authenticated:
        return {}
    inbox_unread = request.user.received_messages.filter(is_read=False).count()
    pending_requests = request.user.received_friend_requests.filter(status="pending").count()
    return {
        "messaging_unread": inbox_unread,
        "messaging_pending_requests": pending_requests,
    }
