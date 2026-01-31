from typing import Any
from unittest import TestCase

from django.db.models import Model
from django.urls import path
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
from rest_framework.authentication import BaseAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from apigatewayauth.authentication import (
    APIGatewayAuthentication,
    APIGatewaySecuritySchemeBase,
)

PATHS = "paths"
COMPONENTS = "components"
SECURITY_SCHEMES = "securitySchemes"
SECURITY = "security"


class SimpleModel(Model):
    pass


class SimpleSerializer(ModelSerializer):
    class Meta:
        model = SimpleModel
        fields = "__all__"


class ScopedAuth(APIGatewayAuthentication):
    ...


class ScopedScheme(APIGatewaySecuritySchemeBase):
    target_class = ScopedAuth
    name: str = ScopedAuth.__name__
    scopes: dict[str, str] = {"scope": ""}


class UnsecuredView(GenericAPIView):
    serializer_class = SimpleSerializer
    authentication_classes: list[type[BaseAuthentication]] = []

    def get(self, request, format=None):
        ...


class SecuredView(UnsecuredView):
    authentication_classes = [APIGatewayAuthentication]
    permission_classes = [IsAuthenticated]


class ScopedView(SecuredView):
    authentication_classes = [ScopedAuth]

    def get_required_scopes(self) -> list[str]:
        return ["scope"]


class UnsecuredViewset(ReadOnlyModelViewSet):
    queryset = SimpleModel.objects.none()
    serializer_class = SimpleSerializer
    authentication_classes: list[type[BaseAuthentication]] = []


class SecuredViewset(UnsecuredViewset):
    authentication_classes = [APIGatewayAuthentication]
    permission_classes = [IsAuthenticated]


class ScopedViewset(SecuredViewset):
    authentication_classes = [ScopedAuth]

    def get_required_scopes(self) -> list[str]:
        return ["scope"]


def generate_schema(*views: GenericAPIView | type[GenericViewSet]) -> dict[str, Any]:
    patterns = []
    router = SimpleRouter()
    for view in views:
        if isinstance(view, GenericAPIView):
            patterns.append(path(type(view).__name__, view.as_view()))
        else:
            router.register(view.__name__, view, basename=view.__name__)
    patterns += router.urls
    schema = SchemaGenerator(patterns=patterns).get_schema(public=True)
    validate_schema(schema)  # make sure generated schemas are always valid
    return schema


def expected_security_scheme(scopes: dict[str, str]) -> dict[str, Any]:
    return {
        "type": "oauth2",
        "description": "API Gateway client credentials security scheme",
        "flows": {
            "clientCredentials": {
                "tokenUrl": "https://api.apps.cam.ac.uk/oauth2/v1/token",
                "scopes": scopes,
            },
            "authorizationCode": {
                "authorizationUrl": "https://api.apps.cam.ac.uk/oauth2/v1/auth",
                "tokenUrl": "https://api.apps.cam.ac.uk/oauth2/v1/token",
                "scopes": scopes,
            },
        },
    }


UNSCOPED_SCHEME = expected_security_scheme({})

SCOPED_SCHEME = expected_security_scheme({"scope": ""})

UNSCOPED_SECURITY: list[dict[type[BaseAuthentication], list[str]]] = [
    {APIGatewayAuthentication.__name__: []}
]
SCOPED_SECURITY: list[dict[type[BaseAuthentication], list[str]]] = [
    {ScopedAuth.__name__: ["scope"]}
]


class APIGatewayAuthTestCase(TestCase):
    def assert_schema_contains_security_scheme(
        self,
        schema: dict[str, Any],
        expected_scheme: dict[type[APIGatewayAuthentication], dict[str, Any]],
        security_scheme: type[BaseAuthentication] = APIGatewayAuthentication,
    ):
        self.assertIn(COMPONENTS, schema)
        self.assertIn(SECURITY_SCHEMES, schema[COMPONENTS])
        self.assertEqual(
            expected_scheme, schema[COMPONENTS][SECURITY_SCHEMES][security_scheme.__name__]
        )

    def assert_endpoints_include_security(
        self,
        schema: dict[str, Any],
        endpoints: list[str],
        expected_scopes: list[dict[str, list[str]]],
    ):
        for endpoint in endpoints:
            self.assertIn(endpoint, schema[PATHS])
            for operation in schema[PATHS][endpoint]:
                self.assertEqual(expected_scopes, schema[PATHS][endpoint][operation][SECURITY])

    def assert_all_endpoints_checked(self, schema: dict[str, Any], *tested_endpoints: list[str]):
        expected_paths = set(a for endpoint in tested_endpoints for a in endpoint)
        self.assertEqual(expected_paths, set(schema[PATHS]))

    def test_unauthenticated_view_no_security(self):
        """
        When:
        - DEFAULT_AUTHENTICATION_CLASSES is not defined
        - View does not define authentication_classes
        - APIGatewaySecuritySchemeBase is registered
        Then:
        - Generated schema for view does not include securityScheme
        - Generated schema for view does not include security on
          operations defined by view.
        """
        schema = generate_schema(UnsecuredView())

        self.assertNotIn(SECURITY_SCHEMES, schema[COMPONENTS])
        for endpoint in schema[PATHS]:
            for operation in schema[PATHS][endpoint]:
                self.assertNotIn(SECURITY, operation)

    def test_unauthenticated_viewset_no_security(self):
        """
        When:
        - DEFAULT_AUTHENTICATION_CLASSES is not defined
        - Viewset does not define authentication_classes
        - APIGatewaySecuritySchemeBase is registered
        Then:
        - Generated schema for viewset does not include securityScheme
        - Generated schema for viewset does not include security on
          operations defined by viewset.
        """
        schema = generate_schema(UnsecuredViewset)

        self.assertNotIn(SECURITY_SCHEMES, schema[COMPONENTS])
        for endpoint in schema[PATHS]:
            for operation in schema[PATHS][endpoint]:
                self.assertNotIn(SECURITY, operation)

    def test_authenticated_view_describes_security(self):
        """
        When:
        - View authentication_classes includes APIGatewayAuthentication
        - APIGatewaySecuritySchemeBase is registered
        Then:
        - Generated schema for view includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for view includes security on each operation
          from view
        """
        schema = generate_schema(SecuredView())

        secured_endpoints = ["/SecuredView"]

        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_endpoints_include_security(schema, secured_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, secured_endpoints)

    def test_authenticated_viewset_describes_security(self):
        """
        When:
        - Viewset authentication_classes includes APIGatewayAuthentication
        - APIGatewaySecuritySchemeBase is registered
        Then:
        - Generated schema for viewset includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for viewset includes security on each operation
          from view
        """
        schema = generate_schema(SecuredViewset)
        secured_endpoints = ["/SecuredViewset/", "/SecuredViewset/{id}/"]

        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_endpoints_include_security(schema, secured_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, secured_endpoints)

    def test_authenticated_view_security_generated_with_scopes(self):
        """
        When:
        - View authentication_classes includes APIGatewayAuthentication
        - APIGatewaySecuritySchemeBase is registered
        - View defines 'get_required_scopes' method
        Then:
        - Generated schema for view includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for view includes security on each operation
          from view
        - Generated security on each operation of view includes scopes defined
          on view
        """
        schema = generate_schema(ScopedView())
        secured_endpoints = ["/ScopedView"]

        self.assert_schema_contains_security_scheme(schema, SCOPED_SCHEME, ScopedAuth)
        self.assert_endpoints_include_security(schema, secured_endpoints, SCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, secured_endpoints)

    def test_authenticated_viewset_security_generated_with_scopes(self):
        """
        When:
        - Viewset authentication_classes includes APIGatewayAuthentication
        - APIGatewaySecuritySchemeBase is registered
        - Viewset defines 'get_required_scopes' method
        Then:
        - Generated schema for viewset includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for viewset includes security on each operation
          from viewset
        - Generated security on each operation of view includes scopes defined
          on viewset
        """
        schema = generate_schema(ScopedViewset)
        secured_endpoints = ["/ScopedViewset/", "/ScopedViewset/{id}/"]

        self.assert_schema_contains_security_scheme(schema, SCOPED_SCHEME, ScopedAuth)
        self.assert_endpoints_include_security(schema, secured_endpoints, SCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, secured_endpoints)

    def test_authenticated_view_security_generated_with_specific_scopes(self):
        """
        When:
        - APIGatewaySecuritySchemeBase is registered
        - Two views include APIGatewayAuthentication in authentication_classes
        - View_a defines 'get_required_scopes' method
        - View_b does not define 'get_required_scopes' method
        Then:
        - Generated schema for views includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for views includes security on each operation
          from both views
        - Generated security on each operation of view_a includes scopes defined
          on view
        - Generated security on each operation of view_b does not include scopes,
          as none defined on view
        """
        schema = generate_schema(SecuredView(), ScopedView())

        scoped_endpoints = ["/ScopedView"]
        unscoped_endpoints = ["/SecuredView"]

        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_schema_contains_security_scheme(schema, SCOPED_SCHEME, ScopedAuth)
        self.assert_endpoints_include_security(schema, scoped_endpoints, SCOPED_SECURITY)
        self.assert_endpoints_include_security(schema, unscoped_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, unscoped_endpoints, scoped_endpoints)

    def test_authenticated_viewset_security_generated_with_specific_scopes(self):
        """
        When:
        - APIGatewaySecuritySchemeBase is registered
        - Two viewsets include APIGatewayAuthentication in authentication_classes
        - Viewset_a defines 'get_required_scopes' method
        - Viewset_b does not define 'get_required_scopes' method
        Then:
        - Generated schema for viewsets includes securityScheme from
          APIGatewaySecuritySchemeBase
        - Generated schema for viewsets includes security on each operation
          from both viewsets
        - Generated security on each operation of view_a includes scopes defined
          on viewset
        - Generated security on each operation of view_b does not include scopes,
          as none defined on viewset
        """
        schema = generate_schema(SecuredViewset, ScopedViewset)

        scoped_endpoints = ["/ScopedViewset/", "/ScopedViewset/{id}/"]
        unscoped_endpoints = ["/SecuredViewset/", "/SecuredViewset/{id}/"]

        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_endpoints_include_security(schema, scoped_endpoints, SCOPED_SECURITY)
        self.assert_endpoints_include_security(schema, unscoped_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, unscoped_endpoints, scoped_endpoints)

    def test_prioritised_redefinition_includes_scopes_for_view(self):
        """
        When:
        - APIGatewaySecuritySchemeBase is registered
        - ScopedScheme(OpenApiAuthenticationExtension) is registered with
          `target_class = APIGatewayAuthentication` and priority > 0
        - View authentication_classes includes APIGatewayAuthentication
        Then:
        - Generated schema for view includes securityScheme from ScopedScheme
        - Generated schema for view includes security on each operation
          from view
        """

        class ScopedScheme(APIGatewaySecuritySchemeBase):
            scopes: dict[str, str] = {"foo": ""}
            priority: int = 1

        try:
            schema = generate_schema(SecuredView())
            secured_endpoints = ["/SecuredView"]

            self.assert_schema_contains_security_scheme(
                schema, expected_security_scheme({"foo": ""})
            )
            self.assert_endpoints_include_security(schema, secured_endpoints, UNSCOPED_SECURITY)
            self.assert_all_endpoints_checked(schema, secured_endpoints)

        finally:
            OpenApiAuthenticationExtension._registry.remove(ScopedScheme)
            del ScopedScheme

    def test_prioritised_redefinition_includes_scopes_for_viewset(self):
        """
        When:
        - APIGatewaySecuritySchemeBase is registered
        - ScopedScheme(APIGatewaySecuritySchemeBase) is registered with
          `target_class = APIGatewayAuthentication` and priority > 0
        - Viewset authentication_classes includes APIGatewayAuthentication
        Then:
        - Generated schema for viewset includes securityScheme from
          other ScopedScheme
        - Generated schema for viewset includes security on each operation
          from viewset
        """

        class ScopedScheme(APIGatewaySecuritySchemeBase):
            scopes: dict[str, str] = {"foo": ""}
            priority: int = 1

        try:
            schema = generate_schema(SecuredViewset)
            secured_endpoints = ["/SecuredViewset/", "/SecuredViewset/{id}/"]

            self.assert_schema_contains_security_scheme(
                schema, expected_security_scheme({"foo": ""})
            )
            self.assert_endpoints_include_security(schema, secured_endpoints, UNSCOPED_SECURITY)
            self.assert_all_endpoints_checked(schema, secured_endpoints)

        finally:
            OpenApiAuthenticationExtension._registry.remove(ScopedScheme)
            del ScopedScheme

    def test_views_independent(self):
        """
        When:
        - BaseAuthentication_a is in the authentication_classes of view_a,
          and described by OpenApiAuthenticationExtension_a, which is registered
        - BaseAuthentication_b is in the authentication_classes of view_b,
          and described by OpenApiAuthenticationExtension_b, which is registered
        Then:
        - Generated schema for views includes securitySchemes described by
          OpenApiAuthenticationExtension_a and OpenApiAuthenticationExtension_b
        - Generated schema for view_a and view_b includes security on each operation
          from both views
        - Generated security on each operation of view_a references securityScheme
          defined on OpenApiAuthenticationExtension_a
        - Generated security on each operation of view_b references securityScheme
          defined on OpenApiAuthenticationExtension_b
        """
        schema = generate_schema(ScopedView(), SecuredView())

        scoped_endpoints = ["/ScopedView"]
        unscoped_endpoints = ["/SecuredView"]

        self.assert_schema_contains_security_scheme(schema, SCOPED_SCHEME, ScopedAuth)
        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_endpoints_include_security(schema, scoped_endpoints, SCOPED_SECURITY)
        self.assert_endpoints_include_security(schema, unscoped_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, scoped_endpoints, unscoped_endpoints)

    def test_viewsets_independent(self):
        """
        When:
        - BaseAuthentication_a is in the authentication_classes of viewset_a,
          and described by OpenApiAuthenticationExtension_a, which is registered
        - BaseAuthentication_b is in the authentication_classes of viewset_b,
          and described by OpenApiAuthenticationExtension_b, which is registered
        Then:
        - Generated schema for viewsets includes securitySchemes described by
          OpenApiAuthenticationExtension_a and OpenApiAuthenticationExtension_b
        - Generated schema for viewset_a and viewset_b includes security on each
          operation from both viewsets
        - Generated security on each operation of viewset_a references securityScheme
          defined on OpenApiAuthenticationExtension_a
        - Generated security on each operation of viewset_b references securityScheme
          defined on OpenApiAuthenticationExtension_b
        """

        schema = generate_schema(SecuredViewset, ScopedViewset)

        scoped_endpoints = ["/SecuredViewset/", "/SecuredViewset/{id}/"]
        unscoped_endpoints = ["/ScopedViewset/", "/ScopedViewset/{id}/"]

        self.assert_schema_contains_security_scheme(schema, SCOPED_SCHEME, ScopedAuth)
        self.assert_schema_contains_security_scheme(schema, UNSCOPED_SCHEME)
        self.assert_endpoints_include_security(schema, unscoped_endpoints, SCOPED_SECURITY)
        self.assert_endpoints_include_security(schema, scoped_endpoints, UNSCOPED_SECURITY)
        self.assert_all_endpoints_checked(schema, unscoped_endpoints, scoped_endpoints)
