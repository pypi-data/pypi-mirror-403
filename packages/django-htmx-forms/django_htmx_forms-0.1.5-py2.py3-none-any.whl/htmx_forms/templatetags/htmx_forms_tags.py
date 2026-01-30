from django import template
from django.forms import Field
from django.forms.boundfield import BoundField
from ..conf import get_setting

register = template.Library()


@register.simple_tag(takes_context=True)
def render_form_field(context, field, css_class="", html_fragment="", **attrs):
    """
    Usage example in a template:

        {% render_form_field form.username "col-md-6" placeholder="Username" autofocus=True %}
        {% render_form_field form.age "" min=18 max=120 disabled='' %}
        {% render_form_field form.search "form-control-lg" data_controller="search" %}

    Notes:

        - data-* attributes must be passed as data_xyz → they become data-xyz
        - Boolean attributes work (required=True); that is, the key alone
        is included only if and only if the corresponding value is True
        - Works for all widgets

    """
    if not isinstance(field, (Field, BoundField)):
        raise Exception('render_form_field() requires a forms.Field or forms.BoundField')

    # Refine css_class
    css_class_tokens = [
        field.field.widget.attrs.get('class', ''),  # classes already in the widget
        "form-control",                             # those we want to add automatically
        css_class,                                  # those requested by the caller
        'is-invalid' if field.errors else '',       # any error ?
    ]
    css_class = ' '.join(css_class_tokens).strip()

    # Apply ccs_class
    if css_class:
        field.field.widget.attrs.update({"class": css_class, })

    # Apply attrs supplied by the caller
    field.field.widget.attrs.update(attrs)

    # Add the extra html_fragment from Form, when available
    form = getattr(field, "form", None)
    html_fragment += form.get_field_html_fragment(field) if form and hasattr(form, "get_field_html_fragment") else ""

    # Select and render template
    template_name = field.form.get_form_field_template(field) if form and hasattr(form, "get_form_field_template") else get_setting("FORM_FIELD_TEMPLATE_NAME")
    ctx = {
        **context.flatten(),  # mantiene request + contesto corrente
        "field": field,
        "html_fragment": html_fragment,
    }
    return template.loader.render_to_string(template_name, ctx)
