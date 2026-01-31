# Django
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Third party
from luhncheck import is_luhn


def clean(value):
    # Remove all non-digits characters
    if not value:
        return ""
    return "".join([char for char in str(value) if char.isdigit()])


class SIRETField(forms.CharField):
    def to_python(self, value):
        return clean(value)

    def bound_data(self, data, initial):
        return clean(super().bound_data(data, initial))

    def validate(self, value):
        length = len(value)
        if length != 14:
            raise ValidationError(
                _(f"SIRET must be 14 chars long (yours is {length})."),
                code="invalid",
            )
        if not is_luhn(value):
            raise ValidationError(
                _("SIRET is not valid."),
                code="invalid",
            )


class SIRENField(forms.CharField):
    def to_python(self, value):
        return clean(value)

    def bound_data(self, data, initial):
        return clean(super().bound_data(data, initial))

    def validate(self, value):
        length = len(value)
        if length != 9:
            raise ValidationError(
                _(f"SIREN must be 9 chars long (yours is {length})."),
                code="invalid",
            )
        if not is_luhn(value):
            raise ValidationError(
                _("SIREN is not valid."),
                code="invalid",
            )
