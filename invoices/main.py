"""Main module for NextDNS Invoices."""

import json
from io import StringIO
from pathlib import Path

import pendulum
import pyotp
import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from box import Box
from jinja2 import Template
from loguru import logger
from requests.auth import HTTPBasicAuth

from invoices.settings import settings

identity = DefaultAzureCredential()
keyvault_client = SecretClient(
    vault_url=str(settings.keyvault_url), credential=identity
)


class NextDNS:
    """Manages NextDNS."""

    def __init__(self) -> None:
        """Initialise NextDNS."""
        self.timeout: int = 5

    def login(self) -> dict[str, str]:
        """Login to NextDNS."""
        nextdns_secret: Box = Box(
            json.loads(keyvault_client.get_secret("nextdns").value)
        )
        otp = pyotp.TOTP(nextdns_secret["nextdns_otp"])
        data = {
            "email": nextdns_secret["nextdns_email"],
            "password": nextdns_secret["nextdns_password"],
            "code": otp.now(),
        }
        r = requests.post(
            "https://api.nextdns.io/accounts/@login",
            json=data,
            headers={"Origin": "https://my.nextdns.io"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.cookies.get_dict()

    def get_account_info(self) -> dict:
        """Get Account Info from NextDNS."""
        login = self.login()
        r = requests.get(
            "https://api.nextdns.io/account",
            headers={
                "Origin": "https://my.nextdns.io",
                "Cookie": f"sid={login['sid']}; pst={login['pst']}",
            },
            timeout=self.timeout,
        )
        code = r.json()["invoices"][0]["code"]
        r.raise_for_status()
        r = requests.get(
            f"https://api.nextdns.io/account/invoice/{code}",
            headers={
                "Origin": "https://my.nextdns.io",
                "Cookie": f"sid={login['sid']}; pst={login['pst']}",
            },
            timeout=self.timeout,
        )

        response = r.json()

        code = response["code"]
        created_on = response["createdOn"]
        amount = response["amount"]
        period_from = response["period"]["from"]
        period_to = response["period"]["to"]

        with Path.open("invoices/template.html", "r") as file:
            template = Template(file.read()).render(
                invoice_id=code.upper(),
                created_on=pendulum.from_timestamp(int(created_on)).format(
                    "MMMM D, YYYY"
                ),
                price_total=amount,
                period_start=pendulum.from_timestamp(int(period_from)).format(
                    "MMMM D, YYYY"
                ),
                period_end=pendulum.from_timestamp(int(period_to)).format(
                    "MMMM D, YYYY"
                ),
            )

        output = StringIO()
        output.write(template)

        return output

    def send_email_via_mailgun(self) -> None:
        """Send an email via Mailgun."""
        f = self.get_account_info().getvalue()

        mailgun_secret: Box = Box(
            json.loads(keyvault_client.get_secret("mailgun").value)
        )

        logger.info("Sending email via Mailgun")
        r = requests.post(
            f"{mailgun_secret['MAILGUN_API']}/{mailgun_secret['MAILGUN_DOMAIN']}/messages",
            auth=HTTPBasicAuth("api", mailgun_secret["MAILGUN_API_KEY"]),
            data={
                "from": str(settings.mailgun_from),
                "to": str(settings.mailgun_to),
                "subject": "NextDNS Invoice",
                "html": f,
            },
            timeout=100,
        )
        r.raise_for_status()
