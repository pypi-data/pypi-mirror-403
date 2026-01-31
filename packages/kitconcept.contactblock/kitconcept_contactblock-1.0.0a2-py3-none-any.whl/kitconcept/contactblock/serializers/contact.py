from kitconcept.contactblock.serializers import path_to_object
from plone.dexterity.utils import iterSchemata
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from plone.restapi.interfaces import IFieldSerializer
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest

import uuid


CONTACT_FIELDS = (
    "title",
    "first_name",
    "last_name",
    "office_phone",
    "contact_phone",
    "contact_email",
    "contact_website",
)


def get_field(obj, fieldname):
    """Return the field from any schema on this object, or None."""
    for schema in iterSchemata(obj):
        if fieldname in schema:
            return schema[fieldname]
    return None


@adapter(IBlocks, IBrowserRequest)
@implementer(IBlockFieldSerializationTransformer)
class ContactListBlockSerializer:
    """Annotate serialized blocks with contact data"""

    order = 0  # must run before uid-to-path transform
    block_type = "contactList"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, block: dict):
        hrefList = []

        for item in block.get("hrefList", []):
            if not item.get("href"):
                continue
            # fix for past bug that lost the @id on the list items
            if "@id" not in item:
                item["@id"] = str(uuid.uuid4())
            href = item["href"][0]

            contact = path_to_object(href["@id"])
            if contact is None:
                continue

            href["@id"] = contact.absolute_url()
            fields = list(CONTACT_FIELDS)

            for fieldname in fields:
                field = get_field(contact, fieldname)
                if not field:
                    continue
                serializer = queryMultiAdapter(
                    (field, contact, self.request), IFieldSerializer
                )
                value = serializer()
                href[fieldname] = value
            href["has_email"] = bool(getattr(contact, "contact_email", None))
            hrefList.append(item)
        block["hrefList"] = hrefList
        return block
