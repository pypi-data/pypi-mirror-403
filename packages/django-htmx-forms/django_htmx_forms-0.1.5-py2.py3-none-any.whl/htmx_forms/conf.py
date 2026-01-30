# myapp/conf.py
from django.conf import settings as django_settings

DEFAULTS = {
    "FORM_FIELD_TEMPLATE_NAME": 'htmx_forms/form/form_field.html',
}

#
# Override in your project's settings as follows:
#
#     HTMX_FORMS = {
#         "FORM_FIELD_TEMPLATE_NAME": 'frontend/my_form_field.html',
#     }
#

def get_setting(key: str):
    user_cfg = getattr(django_settings, "HTMX_FORMS", {})
    return user_cfg.get(key, DEFAULTS[key])
