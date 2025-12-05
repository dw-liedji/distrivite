import mistune
from django.utils.safestring import mark_safe

# Create a secure Markdown renderer that only allows basic formatting (no HTML)
markdown_renderer = mistune.create_markdown(
    escape=True,  # Escapes any dangerous HTML
    plugins=[
        "strikethrough",
        "table",
    ],  # Optional: Enables strikethrough & table support
)


def render_markdown(text):
    """Convert consultation text into safe HTML."""
    return mark_safe(markdown_renderer(text))
