from django.urls import path

from . import views

app_name = 'user'
urlpatterns = [
    path('signin/', views.SignIn.as_view(), name='SignIn'),
    path('signup/', views.SignUp.as_view(), name='SignUp'),
    path('logout/', views.user_logout, name='Logout'),
]
