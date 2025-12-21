import json

from django import forms
from django.urls import reverse_lazy


class HTMXSelectWidget(forms.Select):
    template_name = "widgets/htmx_select.html"

    def __init__(self, attrs=None, view_name=None, forwarded_fields=None):
        super().__init__(attrs)
        self.view_name = view_name
        self.forwarded_fields = forwarded_fields or []

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)

        if not self.view_name:
            raise ValueError("view_name is required for HTMXSelectWidget")

        htmx_attrs = {
            "hx-get": reverse_lazy(self.view_name),
            "hx-trigger": "keyup changed delay:300ms",
            "hx-target": "next .autocomplete-results",
            "autocomplete": "off",
            "name": "q",  # Send the input value as `q` in the request
            "hx-vals": json.dumps({"input_id": attrs["id"]}),
        }

        if self.forwarded_fields:
            htmx_attrs["hx-include"] = ", ".join(
                [f"#id_{field}" for field in self.forwarded_fields]
            )

        attrs.update(htmx_attrs)
        return attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Fetch the display value using the field's queryset
        display_value = ""
        if value and hasattr(self, "field"):
            try:
                obj = self.field.queryset.get(pk=value)
                display_value = str(obj)  # Use the model's __str__ method
            except (self.field.queryset.model.DoesNotExist, ValueError):
                pass

        context["widget"].update(
            {
                "display_value": display_value,
                "is_searchable": True,
            }
        )
        return context


class HTMXAutoCompleteWidget(forms.TextInput):
    template_name = "widgets/htmx_autocomplete.html"

    def __init__(self, attrs=None, forwarded_fields=None, view_name=None):
        super().__init__(attrs)
        self.forwarded_fields = forwarded_fields or []
        self.view_name = view_name

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if not self.view_name:
            raise ValueError("view_name is required for HTMXAutoCompleteWidget")

        hx_attrs = {
            "hx-get": reverse_lazy(self.view_name),
            "hx-trigger": "keyup changed delay:300ms",
            "hx-target": "next .htmx-autocomplete-results",
            "hx-vals": json.dumps({"input_id": attrs["id"]}),
            "name": "q",  # Send the input value as `q` in the request
            "autocomplete": "off",  # Disable browser autocomplete
        }

        if self.forwarded_fields:
            forwarded_ids = [f"#id_{field}" for field in self.forwarded_fields]
            hx_attrs["hx-include"] = ", ".join(forwarded_ids)

        attrs.update(hx_attrs)
        return attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["value"] = value  # Pass the initial value to the template
        return context
