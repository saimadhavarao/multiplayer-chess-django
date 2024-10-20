from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # Import to handle user queries
from django.utils.timezone import now  # Import for timezone-aware datetime
from datetime import timedelta  # Import timedelta
from chess_app.models import Profile  # Import Profile model

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
    # Only logged-in users can access this view
    return render(request, 'chess_app/play_game.html')

# View for the game page with active users and game history
@login_required
def game_page(request):
    # Step 1: Update the last activity timestamp for the current user
    Profile.objects.filter(user=request.user).update(last_activity=now())

    # Step 2: Retrieve active users who have been active within the last 10 minutes (excluding the current user)
    ten_minutes_ago = now() - timedelta(minutes=10)
    active_users = Profile.objects.filter(last_activity__gte=ten_minutes_ago).exclude(user=request.user)

    # Step 3: Debugging print statement to see active users in the console
    print(f"Active Users: {active_users}")

    # Step 4: Pass active users to the template
    context = {
        'active_users': active_users,
    }
    return render(request, 'chess_app/game.html', context)
