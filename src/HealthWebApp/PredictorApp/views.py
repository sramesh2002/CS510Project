from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from django.contrib import messages


# Create your views here.
def home(request):
    return render(request, 'home.html')

def results(request):
    if request.method == 'POST':
        age = request.POST.get('ageInput')
        print(age)
        conditions =  request.POST.get('conditionsTextarea')
        race = request.POST.get('raceSelect')
        gender = request.POST.get('gender', 'Not specified')

        return render(request, 'results.html', {
            'age': age,
            'conditions': conditions,
            'race': race,
            'gender': gender
        })
    else:
        return HttpResponse("Invalid request", status=400)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')  # Explicit redirect to 'home'
            else:
                return HttpResponse("Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect back to login page

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, "Signup successful! You can now log in.")
            return redirect('home')
        else:
            messages.error(request, "Signup failed. Please correct the errors below.")         
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
        
        
