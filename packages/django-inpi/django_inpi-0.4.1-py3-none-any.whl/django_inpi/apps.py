# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InpiConfig(AppConfig):
    name = "django_inpi"
    verbose_name = _("Django INPI")
