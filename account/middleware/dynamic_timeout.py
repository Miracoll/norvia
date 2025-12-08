from django.utils.deprecation import MiddlewareMixin

from account.models import Config

class DynamicSessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                config = Config.objects.first()
                timeout = config.session_timeout_minutes if config else 7200
            except:
                timeout = 7200

            request.session.set_expiry(timeout)
