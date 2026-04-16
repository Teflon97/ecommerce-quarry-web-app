from django.urls import path
from . import views

urlpatterns = [
    # Employee CRUD
    path('', views.employee_list, name='employee_list'),
    path('create/', views.employee_create, name='employee_create'),
    path('<uuid:pk>/', views.employee_detail, name='employee_detail'),
    path('<uuid:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('<uuid:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # Service/Delivery dashboard
    path('service-dashboard/', views.service_dashboard, name='service_dashboard'),
    
    # Delivery management
    path('delivery/<uuid:assignment_id>/accept/', views.accept_delivery, name='accept_delivery'),
    path('delivery/<uuid:assignment_id>/update/', views.update_delivery_status, name='update_delivery_status'),
    path('order/<uuid:order_id>/assign-delivery/', views.assign_delivery, name='assign_delivery'),
]