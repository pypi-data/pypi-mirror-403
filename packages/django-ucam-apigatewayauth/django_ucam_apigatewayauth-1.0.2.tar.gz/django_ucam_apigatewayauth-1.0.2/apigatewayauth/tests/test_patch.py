from unittest import TestCase
from unittest.mock import Mock

from identitylib.identifiers import Identifier, IdentifierSchemes
from rest_framework.request import HttpRequest

from apigatewayauth.authentication import (
    APIGatewayAuthentication,
    APIGatewayAuthenticationDetails,
)
from apigatewayauth.patch import dummy_authentication, mock_authentication


class APIGatewayAuthTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.authn = APIGatewayAuthentication()
        self.request: HttpRequest = Mock(spec=HttpRequest)
        self.request.META = {}

    def test_dummy_returns_expected(self):
        with dummy_authentication():
            result = self.authn.authenticate(self.request)
        assert result is not None
        user, details = result
        assert user.username == str(details.principal_identifier)
        assert details.principal_identifier == Identifier("foo", IdentifierSchemes.CRSID)
        assert details.scopes == set()

    def test_mock_returns_expected(self):
        expected_details = APIGatewayAuthenticationDetails(
            principal_identifier=Identifier("Brian", IdentifierSchemes.CRSID), scopes={"read"}
        )
        with mock_authentication(expected_details):
            result = self.authn.authenticate(self.request)
        assert result is not None
        user, details = result
        assert user.username == str(expected_details.principal_identifier)
        assert details == expected_details

    def test_unauthenticated_request_returns_none(self):
        result = self.authn.authenticate(self.request)
        assert result is None
