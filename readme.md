install requirements.txt

if requirements.txt not installed properly install anaconda and run this command.
conda create -n videochat python django pip Pillow psycopg2 -c conda-forge
activate conda env.
pip install channels
pip install django-phonenumber-field
pip install django-phonenumber-field[phonenumbers]
pip install django-redis

run redis:6 in docker or linux system version 5 or above
do migrations
run server

create superuser and update it's profile from admin panel.

login with credentials of user1
go to contacts and add other member using their mobile number or email.

go to user2's notification area and accept user1's friend request.
then both users can talk to eachother, as well as can do audio and video call.

to create group go to discussion area and click + button in top add group name, description and image.
click on group and in menu select 'manage user' and add members from your contacts.
