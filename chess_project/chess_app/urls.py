from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.redirect_login, name='home'),  # Redirect to login or game
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('rules/', views.rules, name='rules'),
    path('login/', auth_views.LoginView.as_view(template_name='chess_app/login.html'), name='login'),  # Login view
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Logout view
    path('join/', views.join_page, name='join'),  # Sign-up (join) page
    path('game/', views.game_page, name='game'),  # Game page with active users list
    path('play_game/', views.play_game, name='play_game'),  # Chessboard page
    path('send_invite/', views.send_invite, name='send_invite'),  # AJAX: Send game invitation
    path('check_invites/', views.check_invites, name='check_invites'),  # AJAX: Check for pending invites
    path('respond_invite/', views.respond_invite, name='respond_invite'),  # AJAX: Accept/Decline an invite
    path('resign_game/', views.resign_game, name='resign_game'),  # New path for resigning the game
]
