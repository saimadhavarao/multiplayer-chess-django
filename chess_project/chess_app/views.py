from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from chess_app.models import Journal, Profile, Invitation, Match, MatchResult
from django.http import JsonResponse
import json

from django.db.models import Q
from chess_app.utils.main_game_logic import ChessLogic

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
    match=Match.objects.filter(id=match_id).first()
    journal=Journal.objects.filter(match=match,user=request.user).first()
    context = {
        'journal':journal,
        'match_id': match_id,   
        'match':match
    }
    return render(request, 'chess_app/play_game.html', context)

@login_required
def custom_logout(request):
    # Set last_activity to a time far in the past, making the user inactive
    Profile.objects.filter(user=request.user).update(last_activity=now() - timedelta(days=365))

    # Log out the user
    logout(request)

    # Redirect to the login page after logout
    return redirect('login')

# View for the game page with active users and match history
@login_required
def game_page(request):
    Profile.objects.filter(user=request.user).update(last_activity=now())
    ten_minutes_ago = now() - timedelta(minutes=10)
    active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user).order_by('-id')
    match_history = MatchResult.objects.filter(player=request.user).order_by('-id')

    context = {
        'active_users': active_users,
        'match_history': match_history,
    }
    return render(request, 'chess_app/game.html', context)

@login_required
def delete_game(request):
    try:
        print('dta',request.body)
        data=json.loads(request.body)
        match_id=data.get('matchId')
        print(match_id)
        match=Match.objects.filter(id=match_id).first()

        match_history=MatchResult.objects.filter(match=match)
        invitation_history=Invitation.objects.filter(match=match)
        if match_history:
            match_history.delete()
        if invitation_history:
            invitation_history.delete()
        match.delete()
        return JsonResponse({'success':True},status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'success':False,'message':f"{str(e)}"},status=400)


@login_required
def check_active_users(request):
    ten_minutes_ago = now() - timedelta(minutes=2)
    #active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user).order_by('-id')
    active_users = Profile.objects.filter(
        last_activity__gte=ten_minutes_ago
    ).exclude(user=request.user)  # Exclude current user

    # Exclude users who have accepted invitations with the current user
    active_users = active_users.exclude(
        Q(user__sent_invitations__status='accepted') |  # Users who sent an accepted invitation
        Q(user__received_invitations__status='accepted')  # Users who received an accepted invitation
    ).order_by('-id')  # Order as needed


    print(active_users)


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
            prev_invitation=Invitation.objects.filter(
            (Q(invitee=invited_user)|Q(inviter=invited_user)),status='accepted'
            )
            if prev_invitation:
                raise Exception("Player is in ongoing game.Please challenge later")

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
        except Exception as e:
            return JsonResponse({'status':'error','message':f"{str(e)}"})
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
        
        accepted_invite = Invitation.objects.filter(
            Q(inviter=request.user) | Q(invitee=request.user),
            status='accepted'
        ).order_by('-id').first()
        #accepted_invite = Invitation.objects.filter(inviter=request.user, status='accepted').order_by('-id').first()
        if accepted_invite and accepted_invite.match:
            # Notify inviter (Player 1) to redirect to the game
            return JsonResponse({'invite': None, 'redirect': True,'match_id': accepted_invite.match.id})
        return JsonResponse({'invite': None, 'redirect': False})

# View for responding to an invite (accept/decline)
@login_required
def respond_invite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        inviter_username = data.get('inviter')
        status = data.get('status')
        print(data,'data')

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
        print(request.POST)
        postData=json.loads(request.body)
        match_id = postData.get('match_id')
        match = Match.objects.get(id=match_id)
        opponent = get_opponent(current_user, match)

        if opponent:
            MatchResult.objects.create(player=current_user,match=match, opponent=opponent, result='lost')
            MatchResult.objects.create(player=opponent,match=match, opponent=current_user, result='won')
            match.active = False
            invitation_instance=Invitation.objects.get(match=match)
            invitation_instance.status='finished'
            invitation_instance.save()
            match.save()

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No active opponent found.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# View for retrieving the current board state
@login_required
def get_game_state(request, match_id):
    try:
        match = Match.objects.get(id=match_id)
        chess_match=ChessLogic(match)
        current = match.player1.username if match.nos_of_moves % 2 == 0 else match.player2.username
        match_result=MatchResult.objects.filter(player=match.player1,opponent=match.player2).order_by('-id').first()
        
        outcome = 'ongoing'
        if not match.active:
            if match_result.result == 'draw':
                outcome = 'draw'
            elif match_result.result=="won":
                if match_result.player==request.user:
                    outcome='won'
                else:
                    outcome='lost'
            elif match_result.result=='lost':
                if match_result.player==request.user:
                    outcome='lost'
                else:
                    outcome='won'
            invitation_instance=Invitation.objects.get(match=match)
            invitation_instance.status='finished'
            invitation_instance.save()
 
        return JsonResponse({'status': 'success', 
                             'board_state':chess_match.get_board_state(),
                             'current':current,
                             'game_active':  match.active,
                             'outcome': outcome,
                             })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': 'Match not found or is inactive'})

chess_match=ChessLogic()
# View for updating the board after a move
@login_required
def update_board(request, match_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        src = data.get('src')
        dst = data.get('dst')

        try:
            match = Match.objects.get(id=match_id, active=True)
            chess_match=ChessLogic(match)
            response_data = update_game_state(request,match, src, dst)
            if (not response_data.get("success")):
                raise Exception(response_data.get('error'))

            return JsonResponse({'status': 'success',
                                 'match_is_active':response_data.get('is_match_active'),
                                 'game_state': response_data.get('outcome'),
                                 'board_state':chess_match.get_board_state()})
        except Exception as e:
            print(e)
            return JsonResponse({'status': 'error', 'message': f'Match not found {str(e)}'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# Helper function to update board state
def update_game_state(request,match, src, dst):
    try:
        chess_match = ChessLogic(match)
        user_outcome=""
        if not match.active:
            return {'success': False, 'error': 'Game is already over'}
        if chess_match.check_is_valid(src, dst):
            match.nos_of_moves+=1
            match.save()
            chess_match.move(src, dst)
            match_opponent_outcome=""
            if chess_match.is_game_over():
                match.active = False
                result = chess_match.get_result()
                if result == '1-0':  
                    match_outcome = 'won'
                    match_opponent_outcome = 'lost'
                    user_outcome = 'won' if request.user == match.player1 else 'lost'
                elif result == '0-1':  
                    match_outcome = 'lost'
                    match_opponent_outcome = 'won'
                    user_outcome = 'won' if request.user == match.player2 else 'lost'
                else:  # Draw
                    match_outcome = 'draw'
                    match_opponent_outcome = 'draw'
                    user_outcome = 'draw'
                match.save()
                MatchResult.objects.create(player=match.player1,match=match,opponent=match.player2,result=match_outcome)
                MatchResult.objects.create(player=match.player2,match=match,opponent=match.player1,result=match_opponent_outcome)
 

            return {
                        'success': True,
                        'is_match_active':  match.active,
                        'outcome': user_outcome
                    }
        else:
                return {'success': False, 'error': 'Invalid move'}
    except Exception as e:
        print(e)
        return {'success': False, 'error': f'Invalid move{str(e)}'}

def edit_match(request, match_id):
    try:
        match = Match.objects.filter(id=match_id).first()
        journal,created=Journal.objects.get_or_create(match=match,user=request.user)
        if request.method == 'POST':
            data=json.loads(request.body)
            journal.journal = data.get('journal', '')
            journal.save()
            return JsonResponse({'success':True},status=200)
        return render(request, 'chess_app/edit-match.html', {'journal': journal})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False,'error':f"{str(e)}"},status=400)




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
