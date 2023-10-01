# import os
import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

# from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import gettext as _

from settings.models import CreateTimeStamp, UpdateTimeStamp

# Create your models here.


# generate path for message media to save in seperate folder for each group
def chat_message_media_upload_path(instance, filename):
    return "group_media/{0}/{1}".format(
        str(instance.room_member.room.room_number), filename
    )


class Room(CreateTimeStamp, UpdateTimeStamp):
    available_choices = (("P", "Personal"), ("G", "Group"))
    room_number = models.UUIDField(editable=False, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to="group_images", blank=True, null=True)
    room_type = models.CharField(max_length=1, choices=available_choices)

    def __str__(self):
        return (
            "room-type: "
            + str(self.room_type)
            + " room-number: "
            + str(self.room_number)
        )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Room, self).save(*args, **kwargs)

    def delete(self):
        # remove images before deleting member
        try:
            self.image.storage.delete(self.image.name)
        except Exception as ex:
            print(ex)
        super(Room, self).delete()

    def clean(self):
        errors = {}
        if self.room_type == "G":
            if self.name is None:
                errors["name"] = _("Name field is required")

            if self.description is None:
                errors["description"] = _("Description field is required")

            if self.image is None:
                errors["image"] = _("Image field is required")

        else:
            if self.name is not None:
                errors["name"] = _("Name Field must be None")

            if self.description is not None:
                errors["description"] = _("Description Field must be None")

            if self.image is not None:
                errors["image"] = _("Image Field must be None")

        print(len(errors))
        if len(errors):
            raise ValidationError(errors)
        super(Room, self).clean()

    def get_last_message(self):
        last_messagee = (
            self.roommember_set.order_by("-message__created_at")
            .last()
            .message_set.order_by("-created_at")
            .first()
        )
        return last_messagee

    def get_online_member(self):
        room_members = self.roommember_set.filter(is_online=True)
        return room_members


class RoomMember(CreateTimeStamp, UpdateTimeStamp):
    member = models.ForeignKey("user.User", on_delete=models.CASCADE)
    room = models.ForeignKey("chat.Room", on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)

    class Meta:
        unique_together = (("member", "room"),)

    def __str__(self):
        return str(self.member.get_full_name()) + " " + str(self.room)

    def save(self, *args, **kwargs):
        if not self.id:
            if self.room.roommember_set.count() == 2 and self.room.room_type == "P":
                return
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(RoomMember, self).save(*args, **kwargs)

    def clean(self):
        if not self.id:
            if self.room.roommember_set.count() == 2 and self.room.room_type == "P":
                raise ValidationError(
                    "Could not add morethen 2 member in personal chat"
                )

    @staticmethod
    def current_room_member_acc_created_at(instance):
        member_list = RoomMember.objects.filter(room=instance.room).order_by(
            "created_at"
        )
        return member_list

    def delete(self):
        # get member list in ace order of create timestamp exlude self from the list
        member_list = (
            RoomMember.objects.filter(room=self.room)
            .order_by("created_at")
            .exclude(id=self.id)
        )

        # create first added member admin.
        if len(member_list):
            new_admin = member_list[0]
            if not new_admin.is_admin:
                new_admin.is_admin = True
                new_admin.save()
            super(RoomMember, self).delete()

        # if there are no other members in the group then remove group after member deletion.
        else:
            room = self.room
            super(RoomMember, self).delete()
            room.delete()


class Message(CreateTimeStamp):
    room_member = models.ForeignKey("chat.RoomMember", on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    media = models.FileField(
        upload_to=chat_message_media_upload_path, blank=True, null=True
    )
    reader = models.ManyToManyField("chat.RoomMember", related_name="reader")

    def __str__(self):
        return "by: " + str(self.room_member)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        return super(Message, self).save(*args, **kwargs)

    def delete(self):
        # remove all media before deleting message
        try:
            self.media.storage.delete(self.media.name)
        except Exception as ex:
            print(ex)
        super(Message, self).delete()

    def reader_user_list(self):
        return self.reader.all().values_list("member", flat=True)


class Contact(CreateTimeStamp):
    owner = models.OneToOneField(
        "user.User", on_delete=models.CASCADE, related_name="owner"
    )
    member = models.ManyToManyField("user.User", blank=True, related_name="member")

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        return super(Contact, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.owner)


class ContactRequest(CreateTimeStamp, UpdateTimeStamp):
    sender = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="sender"
    )
    receiver = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="receiver"
    )
    accepted = models.BooleanField(default="False")

    class Meta:
        unique_together = (("sender", "receiver"),)

    def __str__(self):
        return str(self.sender) + " " + str(self.receiver)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super(ContactRequest, self).save(*args, **kwargs)

    def clean(self):
        if self.sender == self.receiver:
            raise ValidationError("sender and receiver could not be same")
        try:
            contact_request = ContactRequest.objects.get(
                sender=self.receiver, receiver=self.sender
            )
            print(
                contact_request,
                "----------contact request already exist",
                self.receiver,
            )
            raise ValidationError("Accept the invitation sent by current receiver")
        except ObjectDoesNotExist as ode:
            print(ode)
        super(ContactRequest, self).clean()
