from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models.roomchat import Room, RoomMember


# delete all members before delting group
@receiver(pre_delete, sender=Room)
def remove_all_members(sender, instance, using, **kwargs):
    for member in instance.roommember_set.all():
        member.delete()


# delete all messages before deleting group member
@receiver(pre_delete, sender=RoomMember)
def remove_all_messages(sender, instance, using, **kwargs):
    for message in instance.message_set.all():
        message.delete()
