from django import forms
from .widgets import HTMXSelectWidget


class HTMXModelChoiceField(forms.ModelChoiceField):
    widget = HTMXSelectWidget

    def __init__(self, view_name=None, forwarded_fields=None, **kwargs):
        super().__init__(**kwargs)
        self.widget.view_name = view_name
        self.widget.forwarded_fields = forwarded_fields
        self.field = self
