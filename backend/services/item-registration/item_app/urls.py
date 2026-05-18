from django.urls import path
from . import views

urlpatterns = [
    # Issuer endpoints
    path('register/', views.register_item, name='item-register'),
    path('my-items/', views.my_items, name='item-my-items'),
    path('<uuid:item_id>/', views.item_detail, name='item-detail'),
    path('<uuid:item_id>/revoke/', views.revoke_item, name='item-revoke'),

    # Admin endpoints
    path('all/', views.all_items, name='item-all'),
]