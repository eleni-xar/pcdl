from django.contrib.auth import get_user_model #, password_validation
from django.contrib.auth import forms
from django.forms import CharField, PasswordInput

User = get_user_model()

class UsernameField(forms.UsernameField):

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs["autocomplete"] = "off"
        return attrs


class UserCreationForm(forms.UserCreationForm):
    password1 = CharField(
        label="Password",
        strip=False,
        widget=PasswordInput(attrs={"autocomplete": "off"}),
        # help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = CharField(
        label="Password confirmation",
        strip=False,
        widget=PasswordInput(attrs={"autocomplete": "off"}),
        help_text="Enter the same password as before for verification."
    )

    class Meta:
        model = User
        fields = ('username', 'email',)
        field_classes = {"username": UsernameField}


class UserChangeForm(forms.UserChangeForm):

    class Meta:
        model = User
        fields = "__all__"
        field_classes = {"username": UsernameField}
