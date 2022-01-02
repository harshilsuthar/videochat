# from django.db import models
# from settings.models import CreateTimeStamp
# import uuid
# from django.utils import timezone
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.db.models import Q


# class PersonalChat(CreateTimeStamp):
#     message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
#     sender = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name='sender')
#     receiver = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name='receiver')
#     message = models.CharField(max_length=100)
#     media = models.FileField(upload_to='personal_chat', blank=True, null=True)
#     read = models.BooleanField()

#     def __str__(self):
#         return str(self.sender.get_full_name())+' '+str(self.receiver.get_full_name())+' '+str(self.message_id)

#     def save(self, *args, **kwargs):
#         if not self.id:
#             self.created_at = timezone.now()
#         return super(PersonalChat, self).save(*args, **kwargs)

#     def delete(self):
#         # remove all media before deleting message
#         try:
#             self.media.storage.delete(self.media.name)
#         except Exception as ex:
#             print(ex)
#         super(PersonalChat, self).delete()

#     def clean(self):
#         if self.sender == self.receiver:
#             raise ValidationError(_('Sender and Receiver could not be same'))
#         super(PersonalChat, self).clean()

#     @staticmethod
#     def unread_messages_count(current_user):
#         unread_count = PersonalChat.objects.filter(receiver=current_user, read=False).count()
#         return unread_count

#     @staticmethod
#     def get_latest_messages(current_user):
#         final_message_list = []
#         mix_messages = PersonalChat.objects.filter(Q(sender=current_user)|Q(receiver=current_user)).order_by('sender', 'receiver', '-created_at')
#         user_list_sender_receiver = mix_messages.values_list('sender','receiver')
#         user_list = list(set([item for t in user_list_sender_receiver for item in t]))
#         user_list.remove(current_user.id)
#         for user in user_list:
#             latest_message = PersonalChat.objects.filter(Q(sender=current_user, receiver__id=user)|Q(receiver=current_user, sender__id=user)).order_by('-created_at')[0]
#             final_message_list.append(latest_message)

#         return final_message_list
