from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from chess_app.models import Profile, Invitation, MatchResult
from django.http import JsonResponse
import json

# Redirect the home page to login or game depending on authentication
def redirect_login(request):
    if request.user.is_authenticated:
        return redirect('game')  # Redirect to the game page if the user is logged in
    else:
        return redirect('login')  # Redirect to the login page if the user is not logged in

# View for the join (sign-up) page
def join_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login after successful sign-up
    else:
        form = UserCreationForm()
    
    return render(request, 'chess_app/join.html', {'form': form})

# View for the about page
def about(request):
    return render(request, 'chess_app/about.html')

# View for the history of chess page
def history(request):
    return render(request, 'chess_app/history.html')

# View for the rules of chess page
def rules(request):
    return render(request, 'chess_app/rules.html')

# View for the chess game page (protected with @login_required)
@login_required
def play_game(request):
    return render(request, 'chess_app/play_game.html')

# View for the game page with active users and match history
@login_required
def game_page(request):
    # Update the last activity timestamp for the current user
    Profile.objects.filter(user=request.user).update(last_activity=now())

    # Retrieve active users who have been active within the last 10 minutes (excluding the current user)
    ten_minutes_ago = now() - timedelta(minutes=10)
    active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user)

    # Retrieve match history for the logged-in user
    match_history = MatchResult.objects.filter(player=request.user)

    # Pass active users and match history to the template
    context = {
        'active_users': active_users,
        'match_history': match_history,
    }
    return render(request, 'chess_app/game.html', context)

# View for sending an invite
@login_required
def send_invite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        invited_username = data.get('username')
        try:
            invited_user = User.objects.get(username=invited_username)
            # Create or get the existing invitation
            invitation, created = Invitation.objects.get_or_create(
                inviter=request.user,
                invitee=invited_user,
                status='pending'  # Set status to 'pending'
            )
            if created:
                return JsonResponse({'status': 'success', 'message': f'Invite sent to {invited_username}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invitation already pending.'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# View for checking invites (polling for real-time notifications)
@login_required
def check_invites(request):
    try:
        # Check for pending invites
        invite = Invitation.objects.get(invitee=request.user, status='pending')
        return JsonResponse({'invite': {'inviter': invite.inviter.username}})
    except Invitation.DoesNotExist:
        # Check if the invite has been accepted and trigger the redirection
        invite = Invitation.objects.filter(invitee=request.user, status='accepted').first()
        if invite:
            return JsonResponse({'invite': None, 'redirect': True})  # Redirect only if accepted
        return JsonResponse({'invite': None, 'redirect': False})

# View for responding to an invite (accept/decline)
@login_required
def respond_invite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        inviter_username = data.get('inviter')
        status = data.get('status')

        try:
            inviter = User.objects.get(username=inviter_username)
            invite = Invitation.objects.get(inviter=inviter, invitee=request.user, status='pending')

            # Update the invitation status based on the response
            invite.status = status
            invite.save()

            if status == 'accepted':
                # Notify both users to start the game
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Game started',
                    'redirect': True  # Set redirect to True when accepted
                })
            else:
                return JsonResponse({'status': 'success', 'message': 'Invite declined'})

        except (User.DoesNotExist, Invitation.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invite not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# View for resigning the game
@login_required
def resign_game(request):
    if request.method == 'POST':
        # Get the current user's opponent
        current_user = request.user
        opponent = get_opponent(current_user)  # Assume you have a function to get the opponent

        if opponent:
            # Create match results
            MatchResult.objects.create(player=current_user, opponent=opponent, result='Lost')
            MatchResult.objects.create(player=opponent, opponent=current_user, result='Won')

            # Redirect both players to the game history page
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No active opponent found.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
