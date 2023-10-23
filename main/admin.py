from django.contrib import admin
from .models import ChatSession, ChatMessage, UserBalance, FunctionSchema, ChatTemplate, SecretKey, FunctionServer
from django.utils.text import Truncator
from .forms import ChatMessageAdminForm, SecretKeyForm, ChatTemplateAdminForm

class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'function_approval_required', 'flagged', 'created_at')
    search_fields = ('title', 'user__username',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

class ChatMessageAdmin(admin.ModelAdmin):
    form = ChatMessageAdminForm
    list_display = ('id', 'short_session_title', 'username', 'role', 'input_cost', 'output_cost', 'created_at')
    search_fields = ('content', 'session__title', 'session__user__username',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    
    def short_session_title(self, obj):
        return Truncator(obj.session.title).chars(50)
    short_session_title.short_description = 'Session Title'

    def username(self, obj):
        return obj.session.user.username
    username.short_description = 'User'

class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'last_credit')
    search_fields = ['user__username', 'user__email']
    list_filter = ['last_credit']

class FunctionSchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'network_access')
    search_fields = ('name', 'user')

class ChatTemplateAdmin(admin.ModelAdmin):
    form = ChatTemplateAdminForm
    list_display = ('name', 'model', 'temperature', 'user', 'is_public')
    search_fields = ('name', 'user')

class SecretKeyAdmin(admin.ModelAdmin):
    form = SecretKeyForm
    list_display = ('user', 'name', 'is_public')

class FunctionServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'ip_address', 'hostname', 'is_public', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'ip_address', 'hostname')
    list_filter = ('is_public', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

admin.site.register(ChatSession, ChatSessionAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(UserBalance, UserBalanceAdmin)
admin.site.register(FunctionSchema, FunctionSchemaAdmin)
admin.site.register(ChatTemplate, ChatTemplateAdmin)
admin.site.register(SecretKey, SecretKeyAdmin)
admin.site.register(FunctionServer, FunctionServerAdmin)