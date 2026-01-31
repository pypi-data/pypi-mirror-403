from email.message import EmailMessage
from email.utils import formataddr
from kitconcept.contactblock import _
from kitconcept.contactblock import logger
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest
from zope.i18n import translate
from zope.interface import alsoProvides


FEEDBACK_EMAIL_EN = """Sent via: {origin}

Message:
{message}

---
{name}
{email}
"""

FEEDBACK_EMAIL_DE = """Versendet über: {origin}

Nachricht:
{message}

---
{name}
{email}
"""


class PostContactForm(Service):
    """Submit the contact form and send an email to the contact."""

    def reply(self):
        data = json_body(self.request)
        validated = self._validate(data)
        alsoProvides(self.request, IDisableCSRFProtection)
        self._send_email(validated)
        return self.reply_no_content()

    def _translate(self, msg):
        return translate(msg, context=self.request)

    def _validate(self, data):
        subject = data.get("subject")
        message = data.get("message")
        if not subject or not message:
            raise BadRequest(self._translate(_("Please enter a subject and message.")))
        if len(message) > 1000:
            raise BadRequest(
                self._translate(_("The message is limited to 1000 characters."))
            )

        salutation = data.get("salutation")
        name = data.get("name")
        email = data.get("email")
        if not name or not email:
            raise BadRequest(
                self._translate(_("Please enter your name and email address."))
            )

        origin = data.get("origin")
        if not origin:
            raise BadRequest(self._translate(_("Origin URL not found.")))

        return {
            "subject": subject,
            "message": message,
            "salutation": salutation,
            "name": name,
            "email": email,
            "origin": origin,
        }

    def _send_email(self, data):
        lang = api.portal.get_current_language()
        name = (
            f"{data['salutation']} {data['name']}"
            if data.get("salutation")
            else data["name"]
        )

        if lang == "en":
            body = FEEDBACK_EMAIL_EN.format(**data)
            from_name = f"{name} via contact form"
        else:
            body = FEEDBACK_EMAIL_DE.format(**data)
            from_name = f"{name} über Kontaktformular"

        message = EmailMessage()
        message.set_content(body)
        message["Reply-To"] = data["email"]

        from_email = api.portal.get_registry_record("plone.email_from_address")
        recipient_email = getattr(self.context, "contact_email", None)

        if not recipient_email:
            raise BadRequest(
                self._translate(
                    _(
                        "This contact's email address is not known, "
                        "so the message cannot be delivered."
                    )
                )
            )

        try:
            api.portal.send_email(
                body=message.as_bytes(),
                recipient=recipient_email,
                sender=formataddr((from_name, from_email)),
                subject=data["subject"],
                immediate=True,
            )
        except Exception as e:
            logger.exception(f"Unable to send email: {e!s}")
            raise Exception(
                self._translate(
                    _(
                        "error_email",
                        default="Sorry, your message could not be delivered.",
                    )
                )
            ) from e
