from django.urls import path
from .views import CustomLoginView, SignUpView
from django.contrib.auth.views import LogoutView
from .views import home

urlpatterns = [
    path('', home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
]