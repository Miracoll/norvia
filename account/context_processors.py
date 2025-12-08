from .models import Config, Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_on')[:20]
    else:
        notifications = []
    return {
        'notifications': notifications
    }

def global_config(request):
    config = Config.objects.first()
    return {
        'config': config
    }