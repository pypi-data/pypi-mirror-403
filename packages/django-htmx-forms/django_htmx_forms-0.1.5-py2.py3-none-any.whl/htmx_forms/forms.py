from django.template import Template, Context
from .conf import get_setting


class HTMXFormMixin:
    """
    Adds HTMX fields attributes and injects HTML field fragments.

    Usage:

        from django import forms
        from htmx_forms.forms import HTMXFormMixin


        class MyForm(HTMXFormMixin, forms.Form)

            username = forms.CharField()
            password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),)
            ...

            htmx_field_attributes = {
                "username": dict(
                    hx_get="/autocomplete/username/",
                    hx_trigger="keyup delay:300ms",
                ),
                ...
            }

            htmx_field_fragments = {
                "password": \"""
                    <div id="{{ field.id_for_label }}__ac" class="mt-2">
                        <a href="/reset">Forgot password?</a>
                    </div>
                \""",
            }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, cfg in self.htmx_field_attributes.items():
            self.add_htmx(name, **cfg)

    htmx_field_attributes = {}
    htmx_field_fragments = {}
    form_field_template_name = ""
    form_field_template_overrides = {}  # es: {"password": "..."}

    def get_form_field_template(self, field):
        return self.form_field_template_overrides.get(
            field.name,
            self.form_field_template_name or get_setting("FORM_FIELD_TEMPLATE_NAME")
        )

    def _render_template(self, tpl, field):
        html = ""
        if tpl:
            # Context minimale; puoi aggiungere quello che ti serve.
            ctx = Context(
                {
                    "form": self,
                    "field": field,
                },
                autoescape=True,  # default: True
            )
            html = Template(tpl).render(ctx)
        return html

    def add_htmx(self, field_name, **attrs):
        field = self[field_name]
        widget = self.fields[field_name].widget

        html_attrs = {}

        for key, value in attrs.items():
            if key.startswith("hx_"):
                html_key = key.replace("_", "-")
            else:
                html_key = key

            html_attrs[html_key] = self._render_template(value, field)

        # # automatic hx-target
        # if "hx-target" not in html_attrs:
        #     field_id = widget.attrs.get("id", f"id_{field_name}")
        #     html_attrs["hx-target"] = f"#{field_id}__target"

        widget.attrs.update(html_attrs)

    def get_field_html_fragment(self, field):
        tpl = self.htmx_field_fragments.get(field.name, "")
        html = self._render_template(tpl, field)
        return html
