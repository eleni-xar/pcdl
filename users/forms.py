from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.forms import CharField, PasswordInput

User = get_user_model()

class UsernameField(forms.UsernameField):

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs["autocomplete"] = "off"
        return attrs


class CustomPasswordField(CharField):

    def __init__(self, label):
        super().__init__()
        self.label=label
        self.strip=False
        self.widget=PasswordInput(attrs={"autocomplete": "off"})


class UserCreationForm(forms.UserCreationForm):

    password1 = CustomPasswordField(label="Password")
    password2 = CustomPasswordField(label="Confirm password")

    class Meta:
        model = User
        fields = ('username', 'email',)
        field_classes = {"username": UsernameField}


class UserChangeForm(forms.UserChangeForm):

    class Meta:
        model = User
        fields = "__all__"
        field_classes = {"username": UsernameField}


class PasswordResetForm(forms.PasswordResetForm):

    def clean_email(self):
        data = self.cleaned_data['email']

        if not User.objects.filter(email=data).exists():
            raise ValidationError("This email does not exist in our database")

        return data


class SetPasswordForm(forms.SetPasswordForm):

    new_password1 = CustomPasswordField(label="New password")
    new_password2 = CustomPasswordField(label="Confirm new password")


class PasswordChangeForm(SetPasswordForm, forms.PasswordChangeForm):

    old_password = CustomPasswordField(label="Old password")
