from django.urls import path
from . import views

urlpatterns = [
    # Issuer endpoints
    path('register/',                          views.register_item,      name='item-register'),
    path('my-items/',                          views.my_items,           name='item-my-items'),
    path('serial/<str:serial_number>/',        views.item_by_serial,     name='item-by-serial'),
    path('reference/<str:reference_number>/',  views.item_by_reference,  name='item-by-reference'),
    path('<uuid:item_id>/',                    views.item_detail,        name='item-detail'),
    path('<uuid:item_id>/revoke/',             views.revoke_item,        name='item-revoke'),

    # Admin endpoints
    path('all/',                               views.all_items,          name='item-all'),
    path('pending/',                           views.pending_items,      name='item-pending'),
    path('<uuid:item_id>/approve/',            views.approve_item,       name='item-approve'),
    path('<uuid:item_id>/reject/',             views.reject_item,        name='item-reject'),
]