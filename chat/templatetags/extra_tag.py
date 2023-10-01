import pytz
from django import template
from django.conf import settings
from django.utils import timezone

from chat.models.roomchat import RoomMember

register = template.Library()


@register.filter(name="last_chat_time")
def last_chat_time(chattime):
    try:
        local_timezone = pytz.timezone(settings.TIME_ZONE)
        chattime = chattime.astimezone(local_timezone)
        timedelta = timezone.now() - chattime

        if timedelta.days >= 365:
            if timedelta.days // 365 == 1:
                return "a year ago"
            else:
                return "{0} years ago".format(timedelta.days // 365)

        else:
            if timedelta.days >= 2:
                return chattime.strftime("%d %b")
            elif timedelta.days == 1:
                return "yeasterday"
            else:
                print(chattime.strftime("%H:%M"))
                return chattime.strftime("%H:%M")
    except Exception as ex:
        print(ex)
        return ""


@register.simple_tag(name="get_end_user")
def get_end_user(room, current_user):
    end_user = room.roommember_set.all().exclude(member=current_user)
    if len(end_user):
        return end_user[0]
    else:
        return room.roommember_set.none()


@register.simple_tag(name="get_current_room_member")
def get_current_room_member(room, current_user):
    try:
        current_room_member = room.roommember_set.get(member=current_user)
        return current_room_member
    except Exception as ex:
        print(ex)
        return room.roommember_set.none()


@register.filter(name="get_room_member_id")
def get_room_member_id(room_id, user_id):
    try:
        current_room_member = RoomMember.objects.get(
            member__id=user_id, room__id=room_id
        )
        return current_room_member.id
    except Exception as ex:
        print(ex)
        return None
