from django.contrib import admin

from .models.roomchat import *


# Register your models here.
class RoomAdmin(admin.ModelAdmin):
    model = Room
    # fields = ['id', 'group_number', 'name', 'description', 'image', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at', 'id']

    def save_model(self, request, obj, form, change):
        if not obj.id:
            current_user = request.user
            super(RoomAdmin, self).save_model(request, obj, form, change)
            obj.roommember_set.create(member=request.user, room=obj, is_admin=True)
        else:
            super(RoomAdmin, self).save_model(request, obj, form, change)



class RoomMemberAdmin(admin.ModelAdmin):
    model = RoomMember
    list_display = ['room', 'member', 'is_online']
    readonly_fields = ['created_at', 'updated_at']


class MessageAdmin(admin.ModelAdmin):
    model = Message
    readonly_fields = ['created_at']



class ContactAdmin(admin.ModelAdmin):
    model = Contact
    readonly_fields = ['created_at']


class ContactRequestAdmin(admin.ModelAdmin):
    model = ContactRequest
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Room, RoomAdmin)
admin.site.register(RoomMember, RoomMemberAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
