from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('notifications/', views.driver_notifications, name='driver_notifications'),
    path('requests/', views.get_driver_requests, name='get_driver_requests'),
    path('request/<str:request_id>/', views.get_request_details, name='get_request_details'),
    path('request/<str:request_id>/respond/', views.respond_to_request, name='respond_to_request'),
    path('deliveries/', views.get_driver_deliveries, name='get_driver_deliveries'),
    path('delivery/<str:delivery_id>/', views.get_delivery_details, name='get_delivery_details'),  # Add this line
    path('delivery/<str:delivery_id>/update-status/', views.update_delivery_status, name='update_delivery_status'),
    path('update-location/', views.update_driver_location, name='update_driver_location'),
    path('notifications/count/', views.get_notifications, name='get_notifications'),
]