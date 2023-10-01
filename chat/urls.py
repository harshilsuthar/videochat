from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.Index.as_view(), name="Index"),
    path("room_list/", views.get_chat_list, name="RoomList"),
    path("load_discussion_room/", views.load_discussion_room, name="RoomDiscussion"),
    path("load_room_messages/", views.load_room_messages, name="RoomMessages"),
    path("chat_file_upload/", views.chat_file_upload, name="ChatFileUpload"),
    path("get_contact_list/", views.ContactView.as_view(), name="ContactView"),
    path(
        "get_room_or_send_invitation/",
        views.get_room_or_send_invitation,
        name="GetRoomOrSendInvitation",
    ),
    path("list_invitation/", views.list_invitation, name="ListInvitation"),
    path("load_invitation/", views.load_invitation, name="LoadInvitation"),
    path("accept_invitation/", views.accept_invitation, name="AcceptInvitation"),
    path("create_group/", views.create_group, name="CreateGroup"),
    path("manage_group/", views.manage_group, name="ManageGroup"),
    path(
        "group_member_add_list/", views.group_member_add_list, name="GroupMemberAddList"
    ),
    path("add_group_member/", views.add_group_member, name="AddGroupMember"),
    path("remove_group_member/", views.remove_group_member, name="RemoveGroupMember"),
    path("change_avatar", views.change_avatar, name="ChangeAvatar"),
    path("update_profile/", views.update_profile, name="UpdateProfile"),
]
