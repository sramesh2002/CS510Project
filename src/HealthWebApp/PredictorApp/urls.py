from django.urls import path
from PredictorApp import views

urlpatterns = [
    path("", views.home, name='home'),
]