from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError


class MyValidator(ASCIIUsernameValidator):
    regex = r"^[\w\s.@+-]+$"


def validate_file_size(file):
    MAX_SIZE_KB = 10
    if file.size > MAX_SIZE_KB * 1024:
        raise ValidationError(
            f"Image profile cannot be larger than {MAX_SIZE_KB}KB, please reduce the image size!"
        )
