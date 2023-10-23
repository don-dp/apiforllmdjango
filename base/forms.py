from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .helpers import check_turnstile
from django.contrib.auth.forms import UserCreationForm

class EmailUpdateForm(forms.Form):
    email = forms.EmailField(required=True)

class AuthAdminForm(AuthenticationForm):
    def clean(self):
        request = self.request
        if not check_turnstile(request):
            raise forms.ValidationError("Invalid captcha.")
        return super().clean()

class EmailRequiredUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=320)

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)