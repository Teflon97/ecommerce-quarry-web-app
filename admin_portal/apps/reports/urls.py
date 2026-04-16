from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('export/orders/', views.export_orders, name='report_export_orders'),
]