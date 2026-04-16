from django.urls import path, include
from django.shortcuts import redirect
from apps.dashboard import views

urlpatterns = [
    path('', lambda request: redirect('/custom-admin/login/')),
    path('custom-admin/login/', include('apps.authentication.urls')),
    path('custom-admin/portal/', include('apps.dashboard.urls')),
    path('driver/', include('apps.driver.urls')),
    path('api/products/', views.public_api_products, name='public_api_products'),
]