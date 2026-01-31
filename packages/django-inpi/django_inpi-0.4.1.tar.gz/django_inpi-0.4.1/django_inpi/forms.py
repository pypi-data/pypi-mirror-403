# Django
from django import forms

# Local application / specific library imports
from .fields import SIRENField, SIRETField


class SIRETForm(forms.Form):
    siret = SIRETField(label="SIRET")


class SIRENForm(forms.Form):
    siren = SIRENField(label="SIREN")
