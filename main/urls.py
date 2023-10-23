from django.urls import path
from .views import HomePage, Chats, ChatMessageList, FunctionsView, TemplatesView, CreateChatView

urlpatterns = [
    path("", HomePage.as_view(), name="homepage"),
    path("chats/", Chats.as_view(), name="chats"),
    path('api/chats/<int:session_id>/', ChatMessageList.as_view(), name='chat_messages'),
    path("functions/", FunctionsView.as_view(), name="functions"),
    path("templates/", TemplatesView.as_view(), name="templates"),
    path("create-chat/", CreateChatView.as_view(), name="create_chat"),
]