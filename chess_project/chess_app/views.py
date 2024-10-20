from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from chess_app.models import Profile, Invitation, Match, MatchResult
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
def play_game(request, match_id):
    context = {
        'match_id': match_id,   
    }
    return render(request, 'chess_app/play_game.html', context)

# View for the game page with active users and match history
@login_required
def game_page(request):
    Profile.objects.filter(user=request.user).update(last_activity=now())
    ten_minutes_ago = now() - timedelta(minutes=10)
    active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user)
    match_history = MatchResult.objects.filter(player=request.user)

    context = {
        'active_users': active_users,
        'match_history': match_history,
    }
    return render(request, 'chess_app/game.html', context)

@login_required
def check_active_users(request):
    ten_minutes_ago = now() - timedelta(minutes=10)
    active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user)

    users_data = [
        {'username': profile.user.username} for profile in active_users
    ]

    return JsonResponse({'active_users': users_data})

# View for sending an invite
@login_required
def send_invite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        invited_username = data.get('username')
        try:
            invited_user = User.objects.get(username=invited_username)
            invitation, created = Invitation.objects.get_or_create(
                inviter=request.user,
                invitee=invited_user,
                status='pending'
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
        # Check for pending invites for the invitee (Player 2)
        invite = Invitation.objects.get(invitee=request.user, status='pending')
        return JsonResponse({'invite': {'inviter': invite.inviter.username}})
    except Invitation.DoesNotExist:
        # If invitee has no pending invites, check if inviter's invite has been accepted
        accepted_invite = Invitation.objects.filter(inviter=request.user, status='accepted').first()
        if accepted_invite and accepted_invite.match:
            # Notify inviter (Player 1) to redirect to the game
            return JsonResponse({'invite': None, 'redirect': True, 'match_id': accepted_invite.match.id})
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
                # Create a match and link it to the invitation
                match_id = create_match(inviter, request.user)  # Create the match
                invite.match = Match.objects.get(id=match_id)  # Link match to invite
                invite.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Game started',
                    'redirect': True,
                    'match_id': match_id  # Pass match_id to track the match for both users
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
        current_user = request.user
        match_id = request.POST.get('match_id')
        match = Match.objects.get(id=match_id)
        opponent = get_opponent(current_user, match)

        if opponent:
            MatchResult.objects.create(player=current_user, opponent=opponent, result='Lost')
            MatchResult.objects.create(player=opponent, opponent=current_user, result='Won')
            match.active = False
            match.save()

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No active opponent found.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# View for retrieving the current board state
@login_required
def get_board_state(request, match_id):
    try:
        match = Match.objects.get(id=match_id, active=True)
        return JsonResponse({'status': 'success', 'board_state': match.board_state})
    except Match.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Match not found or is inactive'})

# View for updating the board after a move
@login_required
def update_board(request, match_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        src = data.get('src')
        dst = data.get('dst')

        try:
            match = Match.objects.get(id=match_id, active=True)
            board_state = update_board_state(match.board_state, src, dst)
            match.board_state = board_state
            match.save()

            return JsonResponse({'status': 'success', 'board_state': board_state})
        except Match.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Match not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# Helper function to update board state
def update_board_state(board_state, src, dst):
    board_state[dst] = board_state[src]
    board_state[src] = None
    return board_state

# Helper function to create a match
def create_match(user1, user2):
    match = Match.objects.create(
        player1=user1,
        player2=user2,
        board_state={},  # Initialize the board state here
        active=True
    )
    return match.id

# Helper function to get opponent of a player in a match
def get_opponent(user, match):
    if match.player1 == user:
        return match.player2
    elif match.player2 == user:
        return match.player1
    return None
