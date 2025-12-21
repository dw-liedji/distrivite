from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class UserRegistrationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

    # Additional fields for custom signup form
    email = forms.EmailField(max_length=254, label="Email")


class InternalUserRegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]


class UserEditForm(forms.ModelForm):
    # https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
    # phone_number = PhoneNumberField(
    #     region="CM",
    #     widget=PhoneNumberPrefixWidget(
    #         [
    #             ("CM", "Cameroon"),
    #             ("CN", "China"),
    #             ("FR", "France"),
    #             ("CA", "Canada"),
    #         ],
    #     ),
    # )

    class Meta:
        model = User
        fields = ["email", "phone_number", "image"]


class EditUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)

        def get_label(obj):
            permission_name = str(obj).split("|")[2].strip()
            model_name = permission_name.split(" ")[2].strip()
            return "%s | %s" % (model_name.title(), permission_name)

        content_type = ContentType.objects.get_for_model(User)
        self.fields["user_permissions"].queryset = Permission.objects.filter(
            content_type=content_type
        )
        # self.fields["user_permissions"].widget.attrs.update(
        #     {"class": "permission-select"}
        # )

        self.fields["user_permissions"].help_text = None
        self.fields["user_permissions"].label = "Label"
        self.fields["user_permissions"].label_from_instance = get_label

    def save(self, commit=True):
        user_instance = super(EditUserForm, self).save(commit)
        user_instance.save()
        user_instance.user_permissions.set(self.cleaned_data.get("user_permissions"))
        return user_instance

    class Meta:
        model = get_user_model()
        fields = ["email", "user_permissions"]

        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "form-control", "style": "width: 300px;"}
            ),
        }
