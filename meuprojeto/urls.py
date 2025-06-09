from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login'), name='home'),
    path('admin/', admin.site.urls),
    path('', include('meuapp.urls')),
]
