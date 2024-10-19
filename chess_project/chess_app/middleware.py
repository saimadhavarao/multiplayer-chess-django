import time
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get the last activity time from the session
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Check if the last activity was within the active window (e.g., 10 minutes)
                elapsed_time = now() - last_activity
                if elapsed_time > timedelta(minutes=10):
                    request.user.is_active = False
                else:
                    request.user.is_active = True
            else:
                request.user.is_active = True

            # Update the last activity time in the session
            request.session['last_activity'] = now()

        return self.get_response(request)
