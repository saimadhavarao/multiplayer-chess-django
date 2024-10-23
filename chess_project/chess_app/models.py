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


class Match(models.Model):
    player1 = models.ForeignKey(User, related_name='player1_matches', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='player2_matches', on_delete=models.CASCADE)
    nos_of_moves=models.IntegerField(default=0)
    board_state = models.JSONField(default=dict)  # This will store the board state as JSON
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    game_state=models.TextField(default='')

    def __str__(self):
        return f"Match between {self.player1} and {self.player2}"
    
class Invitation(models.Model):
    inviter = models.ForeignKey(User, related_name="sent_invitations", on_delete=models.CASCADE)
    invitee = models.ForeignKey(User, related_name="received_invitations", on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)  # Add match foreign key
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'),('finished','Finished')], default='pending')

    def __str__(self):
        return f"{self.inviter} invited {self.invitee}"
    
class Journal(models.Model):
    journal=models.TextField(default="")
    match=models.ForeignKey(Match,related_name='match_journal',on_delete=models.CASCADE,blank=True,null=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return f"{self.user} invited {self.match}"
 
class MatchResult(models.Model):
    player = models.ForeignKey(User, related_name='matches', on_delete=models.CASCADE)
    match=models.ForeignKey(Match,related_name='result',on_delete=models.CASCADE,blank=True,null=True)
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
