from django.utils.timezone import now
from datetime import timedelta
from chess_app.models import Profile

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            try:
                # Get the last activity time from the Profile model
                last_activity_time = Profile.objects.get(user=request.user).last_activity

                # Check if the user has been inactive for more than 10 minutes
                if now() - last_activity_time > timedelta(minutes=10):
                    request.user.is_active = False  # Mark the user inactive
                else:
                    request.user.is_active = True  # Mark the user active

                # Update the last activity timestamp in the Profile model
                Profile.objects.filter(user=request.user).update(last_activity=now())
                
            except Profile.DoesNotExist:
                # Handle if no Profile exists for the user (this shouldn't happen if profiles are created on user creation)
                Profile.objects.create(user=request.user, last_activity=now())

        # Continue processing the request
        response = self.get_response(request)
        return response
