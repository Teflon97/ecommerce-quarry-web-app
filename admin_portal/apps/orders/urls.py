from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('<uuid:pk>/', views.order_detail, name='order_detail'),
    path('<uuid:pk>/update-status/', views.order_update_status, name='order_update_status'),
]