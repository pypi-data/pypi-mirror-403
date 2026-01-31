# Standard Library
from json import dumps, loads

# Django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Third party
import mureq

# Local application / specific library imports
from .data import get_legal_status_from_json


class INPIApi:
    token = None

    # INIT

    def __init__(self, skip_init=False):
        if not skip_init:
            self.login()

    def test_settings(self):
        if not hasattr(settings, "DJANGO_INPI_USERNAME") or not hasattr(
            settings, "DJANGO_INPI_PASSWORD"
        ):
            raise ImproperlyConfigured(
                "You need to set the DJANGO_INPI_USERNAME and DJANGO_INPI_PASWWORD environments variables"
            )

    def login(self):
        """
        Performs a login against INPI API, setup a token.
        Usage:
            from django_inpi.api import INPIApi; api = INPIApi()
        """
        self.test_settings()

        login_url = (
            settings.DJANGO_INPI_LOGIN_URL
            if hasattr(settings, "INPI_LOGIN_URL")
            else "https://registre-national-entreprises.inpi.fr/api/sso/login"
        )
        body = self.to_bytes(
            {
                "username": settings.DJANGO_INPI_USERNAME,
                "password": settings.DJANGO_INPI_PASSWORD,
            }
        )

        response = mureq.post(login_url, body)

        if response.status_code != 200:
            raise ConnectionError(
                f"INPI api returned a status code {response.status_code}, which is != 200. The INPI API might be down, or your INPI_LOGIN_URL is incorrect."
            )

        response_json = self.bytes_to_dict(response.body)

        if "token" not in response_json:
            raise KeyError(
                "No token was returned by the INPI API. Ensure that your account credentials are corrects."
            )

        self.token = response_json["token"]

    # HELPERS

    def to_bytes(self, var):
        """
        Converts dict & str to bytes (in order to be able to send them using mureq).
        """
        if type(var) is dict:
            return dumps(var).encode("utf-8")
        elif type(var) is str:
            return var.encode("utf-8")

    def bytes_to_dict(self, var):
        """
        Converts bytes content (answer from the api) into a dict that we can use.
        """
        return loads(var.decode("utf-8"))

    def add_value_to_address_txt(self, address_txt, value):
        if value:
            if address_txt != "":
                address_txt += " " + value
            else:
                address_txt += value
        return address_txt

    def get_address_from_json(self, address_json) -> dict:
        street_number = (
            address_json["numVoie"] if address_json["numVoiePresent"] else ""
        )
        street_type = (
            address_json["typeVoie"] if address_json["typeVoiePresent"] else ""
        )
        street_name = address_json["voie"] if address_json["voiePresent"] else ""
        postal_code = (
            address_json["codePostal"] if address_json["codePostalPresent"] else ""
        )
        city = address_json["commune"] if address_json["communePresent"] else ""

        full_address_txt = ""
        full_address_txt = self.add_value_to_address_txt(
            full_address_txt, street_number
        )
        full_address_txt = self.add_value_to_address_txt(full_address_txt, street_type)
        full_address_txt = self.add_value_to_address_txt(full_address_txt, street_name)
        full_address_txt = self.add_value_to_address_txt(full_address_txt, postal_code)
        full_address_txt = self.add_value_to_address_txt(full_address_txt, city)

        return {
            "street_number": street_number,
            "street_type": street_type,
            "street_name": street_name,
            "postal_code": postal_code,
            "city": city,
            "full_address": full_address_txt,
            "country": "FR" if address_json["pays"] == "FRANCE" else None,
        }

    def get_generic_company_data_from_json(self, json) -> tuple[str, dict | None, dict, dict | None]:
        if "personneMorale" in json[0]["formality"]["content"]:
            company_name = json[0]["formality"]["content"]["personneMorale"][
                "identite"
            ]["entreprise"]["denomination"]
            manager_coordinates = {}
            if "composition" in json[0]["formality"]["content"]["personneMorale"]:
                for pouvoir in json[0]["formality"]["content"]["personneMorale"][
                    "composition"
                ]["pouvoirs"]:
                    if (
                        pouvoir["typeDePersonne"] == "INDIVIDU"
                    ):  # if we have the infos of a real person and not a company (which don't have a first name and a last name)
                        manager_coordinates = {
                            "first_name": pouvoir["individu"]["descriptionPersonne"][
                                "prenoms"
                            ][0],
                            "last_name": pouvoir["individu"]["descriptionPersonne"][
                                "nom"
                            ],
                        }
                        break
            address = self.get_address_from_json(
                json[0]["formality"]["content"]["personneMorale"]["adresseEntreprise"][
                    "adresse"
                ]
            )
        elif "personnePhysique" in json[0]["formality"]["content"]:
            manager_coordinates = {
                "first_name": json[0]["formality"]["content"]["personnePhysique"][
                    "identite"
                ]["entrepreneur"]["descriptionPersonne"]["prenoms"][0],
                "last_name": json[0]["formality"]["content"]["personnePhysique"][
                    "identite"
                ]["entrepreneur"]["descriptionPersonne"]["nom"],
            }
            company_name = f"{manager_coordinates['first_name']} {manager_coordinates['last_name']}"
            address = self.get_address_from_json(
                json[0]["formality"]["content"]["personnePhysique"][
                    "adresseEntreprise"
                ]["adresse"]
            )
        else:
            if "exploitation" in json[0]["formality"]["content"]:
                company_name = json[0]["formality"]["content"]["exploitation"][
                    "identite"
                ]["entreprise"]["denomination"]
                address = self.get_address_from_json(
                    json[0]["formality"]["content"]["exploitation"][
                        "etablissementPrincipal"
                    ]["adresse"]
                )
            else:
                address = None
                company_name = ""
            manager_coordinates = {
                "first_name": "",
                "last_name": "",
            }
        legal_status = get_legal_status_from_json(json)

        return company_name, address, manager_coordinates, legal_status

    # API CALLS

    def get(self, siret=None, siren=None):
        """
        Does a GET request on the INPI API with a SIREN (from a SIRET or directly through the SIREN), returns company info if found.
        TODO: handle the case where we have a 429 (too many requests), since an account is limited at 10k requests per day
        """

        if siret and siren:
            raise ImproperlyConfigured(
                "You can only send a siret OR a siren, not the two at the same time."
            )
        elif siret:
            # the API uses only the siren, so we can convert the siret into the siren number
            # a siret can never start by a 0 so we're good
            siren = int(str(siret)[:9])

        get_url = f"https://registre-national-entreprises.inpi.fr/api/companies?page=1&pageSize=1&siren%5b%5d={siren}"
        bearer_token = f"Bearer {self.token}"

        response = mureq.get(get_url, headers={"Authorization": bearer_token})

        if response.status_code != 200:
            raise ConnectionError(
                f"INPI api returned a status code {response.status_code}, which is != 200. The INPI API might be down, or your INPI_LOGIN_URL is incorrect."
            )

        response_json = self.bytes_to_dict(response.body)
        return response_json

    def get_generic_company_data(self, siret=None, siren=None):
        """
        Get only a fraction of the company data (address and the name of the director)
        """

        response_json = self.get(siret, siren)
        if response_json == []:
            raise ValueError("Error, the json returned by the API is empty.")

        company_name, address, manager_coordinates, legal_status = (
            self.get_generic_company_data_from_json(response_json)
        )

        return {
            "name": company_name,
            "legal_status": legal_status,
            "address": address,
            "manager": manager_coordinates,
        }
