from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints — no authentication required
    path('register/', views.register, name='auth-register'),
    path('login/', views.login, name='auth-login'),
    path('token/refresh/', views.token_refresh, name='auth-token-refresh'),

    # Authenticated endpoints — JWT required
    path('logout/', views.logout, name='auth-logout'),
    path('profile/', views.profile, name='auth-profile'),
    path('profile/update/', views.update_profile, name='auth-profile-update'),
    path('change-password/', views.change_password, name='auth-change-password'),
    path('verify/', views.verify_token, name='auth-verify-token'),

    # Admin endpoints
    path('users/', views.list_users, name='auth-list-users'),
    path('users/<uuid:user_id>/deactivate/', views.deactivate_user, name='auth-deactivate-user'),
]