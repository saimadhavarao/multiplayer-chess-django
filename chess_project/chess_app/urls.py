from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Redirect to login or game if user is authenticated
    path('', views.redirect_login, name='home'),  

    # Informational pages
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('rules/', views.rules, name='rules'),

    # Login and Logout views using Django's built-in authentication system
    path('login/', auth_views.LoginView.as_view(template_name='chess_app/login.html'), name='login'),  # Login page
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Logout, redirect to login

    # User registration (sign-up) page
    path('join/', views.join_page, name='join'),  

    # Game-related views
    path('game/', views.game_page, name='game'),  # Game page showing active users and match history
    path('play_game/<int:match_id>/', views.play_game, name='play_game'),  # Chess game page by match_id
    path('delete_game/', views.delete_game, name='delete_game'),  
    path('edit-match/<int:match_id>/', views.edit_match, name='edit_match'),  
    
    # AJAX requests for sending/handling invitations and board state
    path('send_invite/', views.send_invite, name='send_invite'),  # AJAX: Send game invitation
    path('check_invites/', views.check_invites, name='check_invites'),  # AJAX: Check for pending invites
    path('respond_invite/', views.respond_invite, name='respond_invite'),  # AJAX: Accept/decline an invite
    path('resign_game/', views.resign_game, name='resign_game'),  # AJAX: Resign from a game
    path('get_game_state/<int:match_id>/', views.get_game_state, name='get_game_state'),  # Poll for board state
    path('update_board/<int:match_id>/', views.update_board, name='update_board'),  # Update board after move

    # Polling active users (for keeping the list updated)
    path('check_active_users/', views.check_active_users, name='check_active_users'),  # Poll active users
]
