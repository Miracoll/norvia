from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_on')[:20]
    else:
        notifications = []
    return {
        'notifications': notifications
    }
