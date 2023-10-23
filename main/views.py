from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import ChatSession, ChatMessage, FunctionSchema, ChatTemplate, FunctionServer
from django.db.models import Max, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from .forms import ChatSessionCreateForm
from django.core.exceptions import ObjectDoesNotExist

class HomePage(View):
    def get(self, request):
        return render(request, 'main/homepage.html')

class Chats(LoginRequiredMixin, View):
    def get(self, request):
        chat_sessions = ChatSession.objects.filter(user=request.user).annotate(latest_message_time=Max('messages__created_at')).order_by(F('latest_message_time').desc(nulls_last=True))
        if chat_sessions.exists():
            first_chat_session = chat_sessions.first()
            chat_messages = ChatMessage.objects.filter(session=first_chat_session).order_by('created_at')
            
        else:
            first_chat_session = None
            chat_messages = []

        return render(request, 'main/chats.html', {'chat_sessions': chat_sessions, 'chat_messages': chat_messages,})

class ChatMessageList(LoginRequiredMixin, View):
    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(pk=session_id)
            if session.user != request.user:
                return JsonResponse({'error': 'Not authorized.'}, status=403)

            chat_messages = ChatMessage.objects.filter(session=session).order_by('created_at')
            chat_data = list(chat_messages.values('role', 'content', 'created_at'))
            
            return JsonResponse(chat_data, safe=False)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found.'}, status=404)
        
class FunctionsView(View):
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        functions_list = FunctionSchema.objects.all().order_by('-created_at')

        paginator = Paginator(functions_list, 10)
        functions = paginator.get_page(page_number)

        return render(request, 'main/functions.html', {'functions': functions})

class TemplatesView(View):
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        templates_list = ChatTemplate.objects.all().order_by('-created_at')

        paginator = Paginator(templates_list, 10)
        templates = paginator.get_page(page_number)

        return render(request, 'main/templates.html', {'templates': templates})

class CreateChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = ChatSessionCreateForm(user=request.user)
        return render(request, 'main/create_chat.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = ChatSessionCreateForm(request.POST, user=request.user)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.user = request.user

            try:
                chat.function_server = FunctionServer.objects.filter(is_public=True).first()
                if chat.function_server is None:
                    raise ObjectDoesNotExist

                chat.save()
                messages.success(request, "Chat session has been created successfully.")
                return redirect('chats')
            except ObjectDoesNotExist:
                messages.error(request, 'No public Function Servers available.')
                return render(request, 'main/create_chat.html', {'form': form})
        else:
            messages.error(request, 'There was a problem creating the chat session.')
            return render(request, 'main/create_chat.html', {'form': form})