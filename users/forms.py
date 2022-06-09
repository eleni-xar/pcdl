from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.forms import CharField, EmailField, EmailInput, ModelForm, PasswordInput
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions, StrictButton
from crispy_forms.layout import HTML, Layout, Fieldset


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


class UserProfileForm(ModelForm):

    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {"username": UsernameField}

    def __init__(self, disabled=None, *args, **kwargs):

        self.disabled = disabled
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-profileForm'
        if self.disabled:
            for field in self.fields:
                self.fields[field].widget.attrs["disabled"] = "disabled"
        self.helper.layout = Layout(
            Fieldset(
                '{% if form.disabled %}Welcome {{user.username}}{% else %}Edit your profile:{% endif %}',
                'username',
                'email',
            ),
            FormActions(
                HTML(
                    """
                    <a class="btn btn-primary"  href="{% url 'edit_user_profile' username=user.username %}">Edit Profile</a>
                    <a class="btn my-btn-light"  href="{% url 'home' %}">Homepage</a>
                    """
                )
                if self.disabled else
                StrictButton('Save Changes', type='submit', css_class="btn-primary")
            )
        )
