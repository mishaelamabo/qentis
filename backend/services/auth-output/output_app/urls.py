from django.urls import path
from . import views

urlpatterns = [
    # Output generation
    path('generate/',                views.generate_outputs, name='generate-outputs'),
    path('item/<str:item_id>/',      views.get_outputs,      name='get-outputs'),

    # Verification
    path('verify/signature/',        views.verify_signature, name='verify-signature'),
    path('verify/watermark/',        views.verify_watermark, name='verify-watermark'),

    # Health check
    path('health/',                  views.health_check,     name='output-health'),
]