from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_activity = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} - Last activity: {self.last_activity}'

class Invitation(models.Model):
    inviter = models.ForeignKey(User, related_name="sent_invitations", on_delete=models.CASCADE)
    invitee = models.ForeignKey(User, related_name="received_invitations", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"{self.inviter} invited {self.invitee}"
    
class MatchResult(models.Model):
    player = models.ForeignKey(User, related_name='matches', on_delete=models.CASCADE)
    opponent = models.ForeignKey(User, related_name='opponent_matches', on_delete=models.CASCADE)
    result = models.CharField(max_length=10, choices=[('won', 'Won'), ('lost', 'Lost'), ('draw', 'Draw')])
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.player.username} vs {self.opponent.username} - {self.result}'
    
# Signal to create or update profile when a user is created or updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

