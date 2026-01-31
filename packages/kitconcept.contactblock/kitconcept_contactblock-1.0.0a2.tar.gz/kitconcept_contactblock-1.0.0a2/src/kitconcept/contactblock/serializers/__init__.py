from plone import api
from plone.dexterity.content import DexterityContent
from typing import cast
from zExceptions import Unauthorized

import contextlib
import re


RESOLVEUID_RE = re.compile(r"resolveuid/([^/]+)")


def relative_path(href: str) -> str:
    "Convert an absolute URL to a portal-relative path"
    portal = api.portal.get()
    relative = href.replace(portal.absolute_url(), "")
    return relative if relative.startswith("/") else f"/{relative}"


def path_to_object(href: str) -> DexterityContent | None:
    "Resolve a UID-based or portal-relative path to a content item"
    obj = None
    match = RESOLVEUID_RE.search(href)
    if match:
        uid = match.group(1)
        with contextlib.suppress(Unauthorized):
            brains = api.content.find(UID=uid)
            obj = cast(DexterityContent, brains[0].getObject()) if brains else None
    else:
        # we have a non-UID based path
        portal = api.portal.get()
        portal_path = "/".join(portal.getPhysicalPath())
        href = relative_path(href)
        path = f"{portal_path}{href}"
        results = api.content.find(path={"query": path, "depth": 0})
        if results:
            brain = results[0]
            with contextlib.suppress(Unauthorized):
                obj: DexterityContent = brain.getObject()
    return obj
