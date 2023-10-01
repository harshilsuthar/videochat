from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views import View

from .forms import CustomUserCreationForm, LoginForm

# from .models import User


class SignIn(View):
    def get(self, request, *args, **kwargs):
        return render(request, "signin.html", {"form": LoginForm})

    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                return redirect("chat:Index")
            else:
                return render(request, "signin.html", {"form": form})

        else:
            print("not valid======")
            print(form.errors.as_json())
            return render(request, "signin.html", {"form": form})


class SignUp(View):
    def get(self, request, *args, **kwargs):
        return render(request, "signup.html", {"form": CustomUserCreationForm})

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                return redirect("user:SignIn")
            else:
                return render(request, "signup.html", {"form": form})
        except Exception as ex:
            print(ex)
            return render(request, "signup.html", {"form": form})


@login_required
def user_logout(request):
    try:
        logout(request)
        return redirect("user:SignIn")
    except Exception as ex:
        print(ex)
        return redirect("user:SignIn")
