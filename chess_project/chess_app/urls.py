# urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.redirect_login, name='home'),  # Home URL will redirect based on login state
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('rules/', views.rules, name='rules'),
    path('login/', auth_views.LoginView.as_view(template_name='chess_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  
    path('join/', views.join_page, name='join'),
    path('play_game/', views.play_game, name='play_game'),  # Chessboard page
]
