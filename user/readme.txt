add this app in project and do makemigrations to create custom user. whose username = email.

go to settings:
add 'user' in installed_app

add this inside settings.py
AUTH_USER_MODEL = 'user.User'
ACCOUNT_USERNAME_REQUIRED = False


do makemigrations and change 001_intial.py depedancy to ('auth', '__first__') of user app
then run migrate
