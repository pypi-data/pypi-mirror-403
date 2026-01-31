from plone.keyring.interfaces import IKeyManager
from plone.restapi.services import Service
from zope.component import getUtility

import jwt
import time
import uuid


# Wait this many seconds before accepting a form submission.
FORM_DELAY = 5


def make_form_ticket(context_uid: str, base_time: int | None = None) -> str:
    """Create a signed JWT asserting permission to submit a form."""
    if base_time is None:
        base_time = int(time.time())
    sub = str(uuid.uuid4())
    payload = {"aud": context_uid, "sub": sub, "nbf": base_time + FORM_DELAY}
    secret = getUtility(IKeyManager).secret()
    ticket = jwt.encode(payload, secret, algorithm="HS256")
    return ticket


class GetFormTicket(Service):
    """Get a ticket that allows submitting the form later."""

    def reply(self):
        # disable HTTP caching
        self.request.response.setHeader(
            "Cache-Control", "max-age=0, must-revalidate, private"
        )

        ticket = make_form_ticket(self.context.UID())
        return {"ticket": ticket}
