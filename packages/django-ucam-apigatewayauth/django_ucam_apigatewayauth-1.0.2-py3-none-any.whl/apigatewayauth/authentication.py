from logging import getLogger
from typing import TYPE_CHECKING, Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from identitylib.identifiers import Identifier
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import HttpRequest

from .id_token import InvalidIdTokenError, verify_id_token_for_api_backend
from .user import APIGatewayAuthenticationDetails, APIGatewayUser

if TYPE_CHECKING:
    # Avoids circular dependency when referenced in DEFAULT_AUTHENTICATION_CLASSES:
    # [First encountered View] -> ... -> *rest_framework.generics*.View ->
    #   Django loading of Settings, loading classes from strings ->
    #   apigatewayauth.authentication.APIGatewayAuthentication ->
    #   drf_spectacular.openapi.AutoSchema -> *rest_framework.generics*
    from drf_spectacular.openapi import AutoSchema


LOG = getLogger(__name__)


class APIGatewayAuthentication(authentication.BaseAuthentication):
    """
    An Authentication provider which interprets the headers provided by the API Gateway.

    This library expects to only be used within an application that is deployed behind and can
    only be invoked by the API Gateway, and therefore relies on the fact that the headers
    provided are authoritative.

    """

    def authenticate(self, request: HttpRequest):
        if not request.META.get("HTTP_X_API_ORG_NAME", None):
            # bail early if we look like we're not being called by the API Gateway
            return None

        try:
            # We should have "Bearer ..." in the authorization header.
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Bearer token not present")

            # Extract the id token from the API Gateway for verification.
            _, token = auth_header.split(" ")

            expected_audiences = getattr(
                settings,
                "API_GATEWAY_JWT_EXPECTED_AUDIENCE",
                [request.build_absolute_uri("/"), request.build_absolute_uri("/").rstrip("/")],
            )

            trusted_issuers = getattr(settings, "API_GATEWAY_JWT_TRUSTED_ISSUERS", None)
            expected_authorised_parties = getattr(
                settings, "API_GATEWAY_JWT_EXPECTED_AUTHORISED_PARTIES", None
            )
            try:
                verify_id_token_for_api_backend(
                    token,
                    expected_audiences,
                    certs_url=getattr(settings, "API_GATEWAY_JWT_ISSUER_CERTS_URL", None),
                    trusted_issuers=trusted_issuers,
                    expected_authorised_parties=expected_authorised_parties,
                )
            except InvalidIdTokenError as e:
                LOG.info(f"Incoming API token failed verification: {e}")
                raise AuthenticationFailed("Invalid API Gateway token") from e
        except AuthenticationFailed as e:
            if getattr(settings, "API_GATEWAY_ENFORCE_ID_TOKEN_VERIFICATION", False):
                raise e
            else:
                LOG.warning(
                    "API_GATEWAY_ENFORCE_ID_TOKEN_VERIFICATION is False. "
                    f"Allowing incoming request with invalid authentication: {e}"
                )

        if not request.META.get("HTTP_X_API_OAUTH2_USER", None):
            raise AuthenticationFailed("Could not authenticate using x-api-* headers")

        try:
            principal_identifier = Identifier.from_string(
                request.META["HTTP_X_API_OAUTH2_USER"], find_by_alias=True
            )
        except Exception:
            raise AuthenticationFailed("Invalid principal identifier")

        auth = APIGatewayAuthenticationDetails(
            principal_identifier=principal_identifier,
            scopes=set(filter(bool, request.META.get("HTTP_X_API_OAUTH2_SCOPE", "").split(" "))),
            # the following will only be populated for confidential clients
            app_id=request.META.get("HTTP_X_API_DEVELOPER_APP_ID", None),
            client_id=request.META.get("HTTP_X_API_OAUTH2_CLIENT_ID", None),
        )
        user = APIGatewayUser(auth)
        return user, auth


class APIGatewaySecuritySchemeBase(OpenApiAuthenticationExtension):
    """
    Describes the security scheme of the API Gateway authentication to allow drf spectacular
    to propagate the security requirements when using the  APIGatewayAuthentication as an
    authentication provider.
    """

    target_class = APIGatewayAuthentication
    name = APIGatewayAuthentication.__name__
    scopes: dict[str, str] = {}

    def get_security_requirement(self, auto_schema: "AutoSchema") -> dict[str, list[str]]:
        """
        Get the security requirement for a given view from the 'get_required_scopes' method on a
        view.

        """
        return {
            self.name: (
                list(auto_schema.view.get_required_scopes())
                if hasattr(auto_schema.view, "get_required_scopes")
                else []
            )
        }

    def get_security_definition(self, auto_schema: "AutoSchema") -> dict[str, Any]:
        return {
            "type": "oauth2",
            "description": "API Gateway client credentials security scheme",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://api.apps.cam.ac.uk/oauth2/v1/token",
                    "scopes": self.scopes,
                },
                "authorizationCode": {
                    "authorizationUrl": "https://api.apps.cam.ac.uk/oauth2/v1/auth",
                    "tokenUrl": "https://api.apps.cam.ac.uk/oauth2/v1/token",
                    "scopes": self.scopes,
                },
            },
        }
