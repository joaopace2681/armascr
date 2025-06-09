from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import View

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

class SignUpView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'registration/signup.html', {'form': form})

# Create your views here.
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
