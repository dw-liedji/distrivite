from allauth.account.adapter import DefaultAccountAdapter


class SignUpAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=False):
        # Customize the user creation process here
        user = super().save_user(request, user, form, commit=False)

        # Set additional fields on the user model
        user.last_name = form.cleaned_data.get("last_name")
        user.first_name = form.cleaned_data.get("first_name")

        # Check if birth_date was provided
        if form.cleaned_data.get("birth_date"):
            user.birth_date = form.cleaned_data["birth_date"]

        user.save()

        return user
