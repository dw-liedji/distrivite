from django.core.exceptions import ValidationError


def validate_file_size(file):
    """
    Validate that the uploaded file does not exceed the specified size limit.
    """
    max_size_mb = 100  # Set max file size (in KB)
    max_size_bytes = max_size_mb * 1024  # Convert to bytes

    if file.size > max_size_bytes:
        raise ValidationError(f"File size must not exceed {max_size_mb} KB.")
