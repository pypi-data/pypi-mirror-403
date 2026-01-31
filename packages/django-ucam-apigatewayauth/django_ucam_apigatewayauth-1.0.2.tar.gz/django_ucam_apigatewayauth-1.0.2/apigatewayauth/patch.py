from typing import ContextManager
from unittest import mock

from identitylib.identifiers import Identifier, IdentifierSchemes

from apigatewayauth.authentication import APIGatewayAuthenticationDetails
from apigatewayauth.user import APIGatewayUser


def dummy_authentication() -> ContextManager:
    """
    Preconfigured patch to allow tests to bypass authentication,
    returning a non-real user.
    """
    return mock_authentication(
        APIGatewayAuthenticationDetails(
            principal_identifier=Identifier("foo", IdentifierSchemes.CRSID), scopes=set()
        )
    )


def mock_authentication(details: APIGatewayAuthenticationDetails) -> ContextManager:
    """
    Configurable patch to allow tests to bypass authentication,
    returning a user with expected details, e.g to test authorization.
    """
    return mock.patch(
        "apigatewayauth.authentication.APIGatewayAuthentication.authenticate",
        mock.Mock(return_value=(APIGatewayUser(details), details)),
    )
