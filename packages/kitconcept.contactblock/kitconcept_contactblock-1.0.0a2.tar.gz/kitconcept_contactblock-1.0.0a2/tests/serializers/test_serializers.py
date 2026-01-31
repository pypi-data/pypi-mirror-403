from kitconcept.contactblock import serializers
from plone import api
from plone.dexterity.content import DexterityContent

import pytest


@pytest.fixture
def test_content(portal) -> list[DexterityContent]:
    """Create test content items."""
    items = []
    with api.env.adopt_roles(["Manager"]):
        for idx in range(1, 6):
            content = api.content.create(
                container=portal,
                type="Document",
                id=f"test-document-{idx:02d}",
                title=f"Test Document {idx:02d}",
            )
            # Force a given UUID for testing resolveuid links
            setattr(content, "_plone.uuid", f"88b82b6fbfa143c3bd227a99c4bc63{idx:02d}")
            content.reindexObject()
            items.append(content)

    return items


class TestSerializers:
    @pytest.fixture(autouse=True)
    def _setup(self, portal, test_content):
        self.portal = portal
        self.portal_url = portal.absolute_url()
        self.content = test_content

    @pytest.mark.parametrize(
        "href,expected",
        [
            ["http://nohost/plone/test-document-01", "/test-document-01"],
            ["http://nohost/plone/test-document-02", "/test-document-02"],
            ["/test-document-03", "/test-document-03"],
            ["test-document-04", "/test-document-04"],
        ],
    )
    def test_relative_path(self, href: str, expected: str):
        result = serializers.relative_path(href)
        assert result == expected

    @pytest.mark.parametrize(
        "href,expected_id",
        [
            ["http://nohost/plone/test-document-01", "test-document-01"],
            ["http://nohost/plone/test-document-02", "test-document-02"],
            ["/test-document-03", "test-document-03"],
            ["test-document-04", "test-document-04"],
            ["/resolveuid/88b82b6fbfa143c3bd227a99c4bc6304", "test-document-04"],
        ],
    )
    def test_path_to_object(self, href: str, expected_id: str):
        result = serializers.path_to_object(href)
        assert result is not None
        assert result.id == expected_id
