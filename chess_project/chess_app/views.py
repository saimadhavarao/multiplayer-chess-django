from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Redirect the home page to login or play_game depending on authentication
def redirect_login(request):
    if request.user.is_authenticated:
        return redirect('play_game')  # If the user is logged in, redirect to chessboard
    else:
        return redirect('login')  # If the user is not logged in, redirect to login page

# View for the login page
def login_page(request):
    return render(request, 'chess_app/login.html')

# View for the join (sign up) page
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
