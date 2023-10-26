from django import forms
from .models import ChatMessage, SecretKey, ChatTemplate, ChatSession
from django.core.exceptions import ValidationError
from django.db.models import Q

class ChatTemplateAdminForm(forms.ModelForm):
    system_prompt = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ChatTemplate
        fields = '__all__'

class ChatMessageAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ChatMessage
        fields = '__all__'
    
class SecretKeyForm(forms.ModelForm):
    key = forms.CharField()

    class Meta:
        model = SecretKey
        fields = ['user', 'name', 'key', 'is_public']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {})
        if instance:
            initial['key'] = instance.decrypt_key()
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.encrypt_key(self.cleaned_data['key'])
        if commit:
            instance.save()
        return instance
    
class ChatSessionCreateForm(forms.ModelForm):
    template = forms.ModelChoiceField(queryset=ChatTemplate.objects.none())

    class Meta:
        model = ChatSession
        fields = ['title', 'template', 'function_approval_required']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChatSessionCreateForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['template'].queryset = ChatTemplate.objects.filter(
                Q(is_public=True) | Q(user=self.user)).order_by('-user', 'name')

    def save(self, commit=True):
        instance = super(ChatSessionCreateForm, self).save(commit=False)
        instance.user = self.user
        if instance.template.is_public or instance.template.user == self.user:
            if commit:
                instance.save()
            return instance
        else:
            raise ValidationError("You can only select a template that is public or belongs to you.")