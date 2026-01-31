# Django
from django.http import JsonResponse

# Local application / specific library imports
from .api import INPIApi
from .forms import SIRENForm, SIRETForm


class SIRETFormGetAllJsonMixin:
    """
    Defines a base template for a SIRET form (with a SIRETField), and uses the SIRETForm form.
    Calls the INPIApi login() & get() functions, returns the full json.
    You need to add the success url yourself and handle the response from the API.
    """

    template_name = "django_inpi/siret_form.html"
    form_class = SIRETForm

    def form_valid(self, form):
        siret = int(form.cleaned_data["siret"])
        api = INPIApi()
        company_details = api.get(siret=siret)

        return JsonResponse(
            {
                "siret": siret,
                "data": company_details,
            }
        )


class SIRETFormGetGenericCompanyDataMixin:
    """
    Defines a base template for a SIRET form (with a SIRETField), and uses the SIRETForm form.
    Calls the INPIApi login() & get_generic_company_data() functions, returns a formatted json containing only basic company data (name, legal_status, address, manager).
    You need to add the success url yourself and handle the response from the API.
    """

    template_name = "django_inpi/siret_form.html"
    form_class = SIRETForm

    def form_valid(self, form):
        siret = int(form.cleaned_data["siret"])
        api = INPIApi()
        company_details = api.get_generic_company_data(siret=siret)

        return JsonResponse(
            {
                "siret": siret,
                "data": company_details,
            }
        )


class SIRENFormGetAllJsonMixin:
    """
    Defines a base template for a SIREN form (with a SIRENField), and uses the SIRENForm form.
    Calls the INPIApi login() & get() functions, returns the full json.
    You need to add the success url yourself and handle the response from the API.
    """

    template_name = "django_inpi/siren_form.html"
    form_class = SIRENForm

    def form_valid(self, form):
        siren = int(form.cleaned_data["siren"])
        api = INPIApi()
        company_details = api.get(siren=siren)

        return JsonResponse(
            {
                "siren": siren,
                "data": company_details,
            }
        )


class SIRENFormGetGenericCompanyDataMixin:
    """
    Defines a base template for a SIREN form (with a SIRENField), and uses the SIRENForm form.
    Calls the INPIApi login() & get_generic_company_data() functions, returns a formatted json containing only basic company data (name, legal_status, address, manager).
    You need to add the success url yourself and handle the response from the API.
    """

    template_name = "django_inpi/siren_form.html"
    form_class = SIRENForm

    def form_valid(self, form):
        siren = int(form.cleaned_data["siren"])
        api = INPIApi()
        company_details = api.get_generic_company_data(siren=siren)

        return JsonResponse(
            {
                "siren": siren,
                "data": company_details,
            }
        )
