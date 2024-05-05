from django.urls import path
from PredictorApp import views
from django.contrib.auth.views import LoginView, LogoutView
from .views import logout_view

urlpatterns = [
    path('home/', views.home, name='home'),
    path('results/', views.results, name='results'),
    path('', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]
