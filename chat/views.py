from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# from django import http
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.http import (  # HttpRequest,
    Http404,
    HttpResponse,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from user.models import User

from .models.roomchat import Contact, ContactRequest, Message, Room, RoomMember

# Create your views here.


class Index(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")


@login_required
def get_chat_list(request):
    room_list = Room.objects.filter(
        roommember__in=RoomMember.objects.filter(member=request.user)
    )
    return render(request, "sidebar_room_list.html", {"room_list": room_list})


class ContactView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        contact_list, created = Contact.objects.get_or_create(owner=request.user)
        return render(request, "contact.html", {"contact_list": contact_list})

    def post(self, request, *args, **kwargs):
        email_mobile = request.POST.get("email_mobile")
        print(email_mobile)
        try:
            validate_email(email_mobile)
            user = User.objects.get(email=email_mobile)
            contect, created = Contact.objects.get_or_create(owner=request.user)
            if user != request.user:
                contect.member.add(user)
                try:
                    ContactRequest.objects.create(
                        sender=request.user,
                        receiver=user,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                except Exception as ex:
                    print(ex)
                return HttpResponse(201)
            else:
                return HttpResponse(403)
        except ObjectDoesNotExist as ode:
            print(ode)
            return HttpResponse(404)
        except ValidationError as ve:
            print("➡ ve :", ve)
            try:
                if len(email_mobile) == 13:
                    user = User.objects.get(mobile=email_mobile)
                    contect, _ = Contact.objects.get_or_create(owner=request.user)
                    if user != request.user:
                        contect.member.add(user)
                        return HttpResponse(201)
                    else:
                        return HttpResponse(403)
                else:
                    return HttpResponse(422)
            except ObjectDoesNotExist as ode:
                print("➡ ode :", ode)
                return HttpResponse(404)
            except Exception as ex:
                print("➡ ex :", ex)
                return HttpResponse(422)
        except Exception as ex:
            print("➡ ex :", ex)
            return HttpResponse(422)


@login_required
def load_discussion_room(request):
    if request.method == "POST":
        room_number = request.POST.get("room_number")
        try:
            room = Room.objects.get(room_number=room_number)
        except Exception as ex:
            print("➡ ex :", ex)
            room = Room.objects.none()
        if room.room_type == "P":
            return render(request, "personal_chat_area.html", {"room": room})
        else:
            return render(request, "group_chat_area.html", {"room": room})


@login_required
def load_room_messages(request, *args, **kwargs):
    if request.method == "POST":
        room_number = request.POST.get("room_number")
        # page = request.POST.get("page")
        try:
            room = Room.objects.get(room_number=room_number)
            messages = Message.objects.filter(room_member__room=room).order_by(
                "created_at"
            )
            return render(
                request, "messages.html", {"messages": messages, "room": room}
            )
        except Http404 as http404:
            print("could not find room", http404)
            return HttpResponseNotFound("Page Not Found")


@login_required
def chat_file_upload(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        room_number = request.POST.get("room_number")
        user_id = request.POST.get("user_id")
        room_member = RoomMember.objects.get(
            member__id=user_id, room__room_number=room_number
        )
        message = Message.objects.create(room_member=room_member, media=file)
        message.reader.add(room_member)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "chat_" + room_number,
            {
                "type": "file_upload",
                "file_src": message.media.url,
                "file_name": message.media.name,
                "room_number": room_number,
                "user_id": user_id,
                "room_member_image_src": room_member.member.image.url,
                "room_member_first_name": room_member.member.first_name,
            },
        )
        return HttpResponse("ok")


@login_required
def get_room_or_send_invitation(request):
    if request.method == "POST":
        end_user_id = request.POST.get("end_user_id")
        try:
            end_user = User.objects.get(id=end_user_id)
            contact_request = ContactRequest.objects.filter(
                Q(sender=request.user, receiver=end_user)
                | Q(sender=end_user, receiver=request.user)
            )
            if len(contact_request):
                contact_request = contact_request[0]
            else:
                contact_request = ContactRequest.objects.create(
                    sender=request.user, receiver=end_user
                )
            if contact_request.accepted is True:
                room = (
                    Room.objects.filter(Q(roommember__member=end_user))
                    .filter(Q(roommember__member=request.user))
                    .filter(room_type="P")
                )
                if len(room):
                    room = room[0]
                    return JsonResponse(
                        {
                            "message": "User Found",
                            "room_id": room.room_number,
                            "status": 200,
                        }
                    )
                else:
                    return render(
                        request, "send_request_area.html", {"end_user": end_user}
                    )
            else:
                return render(request, "send_request_area.html", {"end_user": end_user})
        except Exception as ex:
            print(ex)
            return JsonResponse({"message": "User Not Found", "status": 404})


@login_required
def list_invitation(request):
    if request.method == "GET":
        contact_request_list = ContactRequest.objects.filter(
            receiver=request.user, accepted=False
        )
        if len(contact_request_list):
            return render(
                request,
                "notification.html",
                {"contact_request_list": contact_request_list},
            )
        else:
            return HttpResponse("No new notification")


@login_required
def load_invitation(request):
    if request.method == "POST":
        invitation_id = request.POST.get("invitation_id")
        print(invitation_id)
        try:
            invitation = ContactRequest.objects.get(id=invitation_id)
            return render(request, "accept_invitation.html", {"invitation": invitation})
        except Exception as ex:
            print("➡ ex :", ex)
            return Http404("Invitation Not Found")


@login_required
def accept_invitation(request):
    if request.method == "POST":
        invitation_id = request.POST.get("invitation_id")
        print(invitation_id)
        try:
            invitation = ContactRequest.objects.get(id=invitation_id)

            # creating room
            room = (
                Room.objects.filter(Q(roommember__member=invitation.sender))
                .filter(Q(roommember__member=invitation.receiver))
                .filter(room_type="P")
            )
            if not len(room):
                room = Room.objects.create(room_type="P")
                RoomMember.objects.create(
                    member=invitation.sender, is_admin=True, room=room
                )
                RoomMember.objects.create(member=request.user, is_admin=True, room=room)

                contact, _ = Contact.objects.get_or_create(owner=invitation.receiver)
                contact.member.add(invitation.sender)

            else:
                room = room[0]
            invitation.accepted = True
            invitation.save()

            # send update disucssion list signal via socket
            update_discussion(invitation.sender.id)
            return render(request, "personal_chat_area.html", {"room": room})
        except Exception as ex:
            print(ex)
            return HttpResponse("Could Not Process Invitaion")


@login_required
def create_group(request):
    if request.method == "POST":
        group_name = request.POST.get("group_name")
        group_description = request.POST.get("group_description")
        group_image = request.FILES.get("group_image")
        print(group_name, group_description, group_image, request.FILES, request.POST)
        if group_name and group_description and group_image:
            room = Room.objects.create(
                name=group_name,
                description=group_description,
                image=group_image,
                room_type="G",
            )
            RoomMember.objects.create(
                member=request.user, room=room, is_admin=True, is_online=True
            )
            return HttpResponse(True)
        else:
            errors = []
            if not group_name:
                errors.append("Group name is mendatory")
            if not group_description:
                errors.append("Group description is mendatory")
            if not group_image:
                errors.append("Group image is mendatory")

            return JsonResponse({"error": errors})


@login_required
def manage_group(request):
    if request.method == "GET":
        room_number = request.GET.get("room_number")
        try:
            room = Room.objects.get(room_number=room_number)
        except Exception as ex:
            print("➡ ex :", ex)
            return JsonResponse({"message": "Room does not exist"})
        try:
            room_member = RoomMember.objects.get(member=request.user, room=room)
            room_member_list = RoomMember.objects.filter(room=room)
            return render(
                request,
                "manage_group.html",
                {
                    "room": room,
                    "room_member_list": room_member_list,
                    "current_member": room_member,
                },
            )
        except Exception as ex:
            print(ex)
            return JsonResponse({"message": "Room Member Does not exist"})


@login_required
def group_member_add_list(request):
    if request.method == "GET":
        room_number = request.GET.get("room_number")
        try:
            room = Room.objects.get(room_number=room_number)
        except Exception as ex:
            print(ex)
            return JsonResponse({"message": "Room does not exist"})
        try:
            room_member = RoomMember.objects.get(room=room, member=request.user)
            if room_member.is_admin is True:
                contact, created = Contact.objects.get_or_create(owner=request.user)
                contact_list = contact.member.all().exclude(
                    id__in=list(
                        RoomMember.objects.filter(room=room).values_list(
                            "member", flat=True
                        )
                    )
                )
                print(contact_list)
                html_response = ""
                if len(contact_list):
                    for member in contact_list:
                        html_response += '<option value="{0}">{1}</option>'.format(
                            member.id, member.get_full_name()
                        )

                return HttpResponse(html_response)
        except Exception as ex:
            print(ex)
            return JsonResponse({"message": "Room Member Does not exist"})


@login_required
def add_group_member(request):
    if request.method == "POST":
        # return JsonResponse({'status':200})

        member_list = request.POST.getlist("member")
        room_number = request.POST.get("room_number")
        print(member_list)
        try:
            room = Room.objects.get(room_number=room_number)
            if len(member_list):
                for member in member_list:
                    try:
                        user = User.objects.get(id=int(member))
                        room_member, created = RoomMember.objects.get_or_create(
                            member=user, room=room
                        )
                        if created:
                            update_discussion(room_member.member.id)
                    except ObjectDoesNotExist as ode:
                        print(ode)
                return JsonResponse({"status": 200})
            update_discussion(room_member.member.id)
            return JsonResponse({"status": 200})
        except ObjectDoesNotExist as ode:
            print(ode)
            return JsonResponse({"status": 404, "message": "Room not exist"})

        except Exception as ex:
            print(ex)
            return JsonResponse({"status": 500, "message": "Something went wrong"})


@login_required
def remove_group_member(request):
    if request.method == "POST":
        room_member_id = request.POST.get("room_member_id")
        try:
            room_member = RoomMember.objects.get(id=room_member_id)
            removing_user_id = room_member.member.id
            current_room_member = RoomMember.objects.get(
                member=request.user, room=room_member.room
            )
            room_number = room_member.room.room_number
            try:
                other_room_members = (
                    RoomMember.objects.filter(room=room_member.room)
                    .exclude(member=room_member.member)
                    .order_by("created_at")
                )
                if current_room_member.is_admin:
                    if len(other_room_members):
                        oldest_room_member = other_room_members[0]
                        if not oldest_room_member.is_admin:
                            oldest_room_member.is_admin = True
                            oldest_room_member.save()
                        if current_room_member == room_member:
                            room_member.delete()
                            update_discussion(removing_user_id)
                            return JsonResponse(
                                {"status": 203, "room_number": room_number}
                            )
                        else:
                            room_member.delete()
                            update_discussion(removing_user_id)
                            return JsonResponse({"status": 202})
                    else:
                        room_member.room.delete()
                        update_discussion(removing_user_id)
                        return JsonResponse({"status": 203, "room_number": room_number})
                elif current_room_member == room_member:
                    room_member.delete()
                    update_discussion(removing_user_id)
                    return JsonResponse({"status": 203})
                else:
                    return JsonResponse({"status": 401})

            except ObjectDoesNotExist as ode:
                print("➡ ode :", ode)
                return JsonResponse({"status": 404})

        except ObjectDoesNotExist as ode:
            print("➡ ode :", ode)
            return JsonResponse({"status": 404})

        except Exception as ex:
            print("➡ ex :", ex)
            return JsonResponse({"status": 500})


def update_discussion(user_id):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "protected_" + str(user_id),
            {
                "type": "update_discussion",
            },
        )
    except Exception as ex:
        print(ex)


def change_avatar(request):
    if request.method == "POST":
        image = request.FILES.get("profile_pic_input")
        print(image, "-----upload image profile")
        if image:
            try:
                user = User.objects.get(id=request.user.id)
                user.image = image
                user.save()
            except ObjectDoesNotExist as ode:
                print(ode)
                return JsonResponse({"status": 404})
            except Exception as ex:
                print(ex)
                return JsonResponse({"status": 500})
            return JsonResponse({"status": 200})
        else:
            return JsonResponse({"status": 400})


def update_profile(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        print(first_name, last_name, email, password1, password2)
        errors = []
        try:
            user = User.objects.get(id=request.user.id)
            if user.password != password1:
                if password1 == password2:
                    if password1 is not None:
                        user.set_password(password1)
                    else:
                        errors.append("Password can't be blank")
                else:
                    errors.append("Both password must be matched")
            try:
                validate_email(email)
                user.email = email
            except Exception as ex:
                print(ex)
                errors.append("Email is not valid")

            if first_name:
                user.first_name = first_name
            else:
                errors.append("First Name can't be blank")

            if last_name:
                user.last_name = last_name
            else:
                errors.append("Last Name can't be blank")

            if len(errors):
                return JsonResponse({"message": errors, "status": 400})
            else:
                user.save()
                return JsonResponse({"status": 200})
        except ObjectDoesNotExist as ode:
            print(ode)
            return JsonResponse({"status": 404})
        except Exception as ex:
            print(ex)
            return JsonResponse({"message": errors, "status": 500})
