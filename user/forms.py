# from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "image", "mobile")

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"

        self.fields["email"].widget.attrs["placeholder"] = "Email Address"
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["first_name"].widget.attrs["placeholder"] = "First Name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        self.fields["last_name"].widget.attrs["placeholder"] = "Last Name"
        self.fields["image"].widget.attrs["placeholder"] = "Profile Picture"
        self.fields["image"].widget.attrs["class"] += " pt-2"
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password"
        self.fields["mobile"].widget.attrs["placeholder"] = "Mobile"


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"

        self.fields["username"].widget.attrs["autocomplete"] = "email"
        self.fields["username"].widget.attrs["placeholder"] = "Email Address"

        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["password"].widget.attrs["placeholder"] = "Password"
