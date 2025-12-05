from djoser.serializers import UserSerializer as BaseUserSerializer
from apps.users.models import User


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "password",
        ]
        read_only_fields = ("username",)

