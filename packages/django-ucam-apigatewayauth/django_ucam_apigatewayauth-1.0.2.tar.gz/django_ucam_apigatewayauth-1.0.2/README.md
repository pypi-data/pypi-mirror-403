# Django API Gateway Authentication

This is a library which contains:

* an authentication provider for Django, allowing the headers passed from the
  [API Gateway](https://developer.api.apps.cam.ac.uk/your-api-here) to be interpreted
  and used within a Django app,
* a set of permissions classes allowing the authentication information provided by the API Gateway
  to be used in authorization decisions throughout an API-based app,

## Library developer quick start

This library is packages using `poetry` and uses our [common Python CI
pipeline](https://gitlab.developers.cam.ac.uk/uis/devops/continuous-delivery/ci-templates/-/blob/master/auto-devops/python.md).
Make sue that `poetry` is installed and bootstrap your local environment via:

```console
$ poetry install
$ poetry run pre-commit install
```

## Required settings

The following Django settings are required to allow this library to be used:

* `PERMISSIONS_SPECIFICATION_URL`, if you plan to enforce authorization using a permissions spec
    this should contain the url (either in the form of a `file://`, `gs://` or `https://` url)
    which contains the permissions spec yaml document,
* `UCAMLOOKUP_USERNAME` and `UCAMLOOKUP_PASSWORD`, these are required if your permissions spec
    contains references to Lookup groups, which this library will need to query Lookup to
    determine membership of these groups.

## Optional settings

The following Django settings can be used to customise how the library authenticates incoming
requests as having been proxied by the API Gateway.

* `API_GATEWAY_ENFORCE_ID_TOKEN_VERIFICATION` - if set to `False`, then a warning is printed to the
    logs if verification failed but the request is allowed to process. If set to `True` then id
    token verification is enforced. For reasons of backwards compatibility, this setting defaults to
    `False` but it is *strongly recommended* that it be enabled.
* `API_GATEWAY_JWT_TRUSTED_ISSUERS` - a list of trusted JWT issuers. The default set
    correspond to Google's OAuth2 id token issuers.
* `API_GATEWAY_JWT_ISSUER_CERTS_URL` - a URL which is used to fetch a JSON document of the form
    `{"[keyid]": "[PEM encoded cert]"}` used to verify id token signatures. The default is to use
    Google's public certificate endpoint.
* `API_GATEWAY_JWT_EXPECTED_AUDIENCE` - the expected audience of the id token. The default is to use
    the base URL of the Django web application as determined by `request.build_absolute_uri()`.
* `API_GATEWAY_JWT_EXPECTED_AUTHORISED_PARTIES` - a list of expected authorised
    parties of the id token. The default is to use a well known set of API Gateway service account
    identities.

## Use in local development

The defaults for the various `API_GATEWAY_...` settings should be suitable for deployment. When
using applications locally, they may need setting. Try to always set
`API_GATEWAY_ENFORCE_ID_TOKEN_VERIFICATION` to `True` if possible. For example, if one is using the
[API Gateway emulator](https://gitlab.developers.cam.ac.uk/uis/devops/api/api-gateway-emulator/),
one can set `API_GATEWAY_JWT_TRUSTED_ISSUERS` to match the issuer configured in the emulator and
point `API_GATEWAY_JWT_ISSUER_CERTS_URL` at the `/certs` endpoint exposed by the emulator.

## Use in tests

To allow test code to access endpoints that would otherwise require authentication, the library
provides a simple way to mock out authentication flow. `dummy_authentication` is pre-configured
with a user that (due to requirements on a CRSid) cannot legitimately exist. It is useful as a
quick drop in to compare [un]authenticated behaviour.

```python
from apigatewayauth.patch import dummy_authentication

def test_api_requires_authn(client: Client, endpoint: str):
    response = client.get(endpoint)
    assert response.status_code == 403
    # test response includes information on how to authenticate

def test_api(client: Client, endpoint: str):
    with dummy_authentication():
        response = client.get(endpoint)
    assert response.status_code == 200
    # test response includes expected data
```

To test endpoints behaviour that should vary depending on the user, `mock_authentication` accepts
a description of the user to mock credentials for, allowing for testing authorization code.

```python
from apigatewayauth.authentication import APIGatewayAuthenticationDetails
from apigatewayauth.patch import mock_authentication

from identitylib.identifiers import Identifier, IdentifierSchemes

def test_api(client: Client, endpoint: str):
    admin_details = APIGatewayAuthenticationDetails(
        principal_identifier=Identifier("admin", IdentifierSchemes.CRSID),
        scopes={"admin", "read", "write"}
    )
    with mock_authentication(admin_details):
        response = client.get(endpoint)
    assert response.status_code == 200
    # test response includes expected data for admin

def test_api(client: Client, endpoint: str):
    other_user = APIGatewayAuthenticationDetails(
        principal_identifier=Identifier("user", IdentifierSchemes.CRSID),
        scopes={"read", "write"}
    )
    with mock_authentication(other_user):
        response = client.get(endpoint)
    assert response.status_code == 200
    # test response includes expected data for user
```

## Expected headers passed from the API Gateway

This library expects the API Gateway to provide the following headers and uses them to determine
the identity of the principal querying an API:

* `x-api-org-name`: the API Gateway organisation name,
  * This library ensures that this is provided by does not make any decisions based on its value,
* `x-api-developer-app-class`: should be the static string `confidential` or `public`,
  * This library ensures that this is provided by does not make any decisions based on its value,
* `x-api_developer-app-id`: the identifier for the developer app created within the API Gateway,
  * This library ensures that this is provided by does not make any decisions based on its value,
* `x-api-oauth2-client-id`: the identifier of the client credentials issued within the API Gateway,
  * This library ensures that this is provided by does not make any decisions based on its value,
* `x-api-oauth2-scope`: a space separated list of oauth2 scopes
  * This is used to determine access to resources within this library
* `x-api-oauth2-user`: the identifier of the user who is making use of the API - this can either be
  a crsid identifier identifying the user who is interacting with the API or an application
  identifier related to the application which is accessing the API.

## Trusting the headers provided by the API Gateway

In order for this library to interpret the headers provided by the API Gateway, add the following
to your restframework settings:

```py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # rely on the API Gateway to provide authentication details
        "apigatewayauth.authentication.APIGatewayAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # make sure that the user is authenticated
        "rest_framework.permissions.IsAuthenticated",
        # ... other permissions classes ...
    ],
}
```

**YOU MUST INCLUDE THE `IsAuthenticated` PERMISSION IF YOU WANT TO DENY UNAUTHENTICATED ACCESS TO
THE API BACKEND.**

This will enforce that any requests to your API have provided the expected headers which the
API Gateway provides to give details about the identity of the principal.

> **NOTE** this library expects that all requests are proxied via the API Gateway, but does not
> authenticate the API Gateway directly. You must ensure that only the API Gateway can contact your
> backend, without this protection the headers which this library uses for authentication can be
> trivially spoofed.

For local development the above headers should be provided in order to allow the information
provided by the API gateway to be mocked.

## Documenting security requirements

This library is integrated with drf_spectacular, allowing generation of OpenAPI specifications of
service endpoints to automatically include security information. When not enforcing scopes, it is
sufficient to simply make use of the `apigatewayauth.authentication.APIGatewayAuthentication` type,
or set is as the `DEFAULT_AUTHENTICATION_CLASSES` key as already described.

The spec may be generated with `manage spectacular`, but may require the following Django setting:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    ...
}
```

## Authorization helpers

This library provides a set of permissions classes which allow authentication decisions to be made
based on the information provided from the API Gateway

### Enforcing scopes

The `HasAnyScope` permissions class can be used to enforce that a client has a token granted by the
API Gateway with any of the given scopes, e.g.:

```py
from rest_framework import viewsets
from apigatewayauth.permissions import HasAnyScope

class ExampleViewSet(viewsets.ReadOnlyModelViewSet):

  permission_classes = [
    # ensure that a client has either the examples.readonly or examples scopes:
    HasAnyScope(
      'https://api.apps.cam.ac.uk/example/examples.readonly',
      'https://api.apps.cam.ac.uk/example/examples'
    )
  ]
```

Scope requirements and capabilities can be propagated into a generated OpenAPI schema description
of the service by creating a custom OpenApiAuthenticationExtension with priority > 0, else the
SecurityScheme is generated without scope information.

```python
from django.apps import AppConfig
from apigateway.authentication import add_scopes_to_scheme
from my_app.scopes import SCOPE_DESCRIPTIONS

class Config(AppConfig):
    name = "my_app"
    verbose_name = "my_app"

    def ready(self):
        class InternalScheme(APIGatewaySecuritySchemeBase):
            scopes: dict[str, str] = SCOPE_DESCRIPTIONS
            priority: int = 1
```

To enforce and document independent sets of scopes, such as deploying an API for your application
and a seperate API for reporting metadata within the same service:

```python
MY_APP_SCOPES = {
    "read": "Read data",
}

class AppAuthentication(APIGatewayAuthentication):
    ...

class AppScheme(APIGatewaySecuritySchemeBase):
    target_class: type[APIGatewayAuthentication] = AppAuthentication
    name: str = AppAuthentication.__name__
    scopes: dict[str, str] = MY_APP_SCOPES
    priority: int = 1

class AppView(APIView):
    authentication_classes = [AppAuthentication]

...

REPORTING_SCOPES = {
    "report": "Read reporting data"
}

class ReportAuthentication(APIGatewayAuthentication):
    ...

class ReportScheme(APIGatewaySecuritySchemeBase):
    target_class: type[APIGatewayAuthentication] = ReportAuthentication
    name: str = ReportAuthentication.__name__
    scopes: dict[str, str] = REPORTING_SCOPES
    priority: int = 1

class ReportView(APIView):
    authentication_classes = [ReportAuthentication]
```

### Enforcing specified permissions

This library includes modules to allow a 'permissions specification' to be read to determine if
a principal has a given permission.

A permissions spec is a yaml document which should contain permission names as keys and the
principals or groups which are granted this permission, e.g.:

```yml
READ_EXAMPLES:
  principals:
    - 1234@application.api.apps.cam.ac.uk
    - wgd23@v1.person.identifiers.cam.ac.uk
  groups:
    - 105217@groups.lookup.cam.ac.uk

WRITE_EXAMPLES:
  principals:
    - abcd@application.api.apps.cam.ac.uk
```

This library provides helpers to allow an app to determine whether a client has been granted a
given permission in a permission spec, e.g.:

```py
from rest_framework import viewsets
from apigatewayauth.permissions import SpecifiedPermission

IsExampleReader = SpecifiedPermission("READ_EXAMPLES")
IsExampleWriter = SpecifiedPermission("WRITE_EXAMPLES")

class ExampleViewSet(viewsets.ModelViewSet):

  def get_permissions(self):
    if self.action in ('retrieve', 'list'):
      self.permission_classes = [IsExampleReader | IsExampleWriter]
    elif self.action in ('create', 'update', 'destroy')
      self.permission_classes = [IsExampleWriter]
    return super().get_permissions()
```

### Limiting actions to 'resource owners'

This library contains a helper permission which allows actions to be limited to resource owners.
This requires integration at the model and queryset level, to allow querysets to be filtered
based on the identity of the principal using the API. This defers decisions about who 'owns' a
given model to the model class. For example:

```py
from django.db import models
from rest_framework import viewsets
from identitylib.identifiers import Identifier

from apigatewayauth.permissions import IsResourceOwningPrincipal



class Example(models.Model):

  name = models.TextField('Name')
  # this field contains the identifier of a principal - e.g. 'wgd23@v1.person.identifiers.cam.ac.uk'
  owner = models.TextField('Owner')

  @staticmethod
  def get_queryset_for_principal(principal_identifier: Identifier):
    """
    This method should return a queryset which limits results to those owned by the principal
    identified by the given identifier. This is used to limit results returned from list endpoints.

    """

    return Example.objects.filter(owner__iexact=str(principal_identifier))

  def is_owned_by(self, principal_identifier: Identifier):
    """
    This method returns whether an instance of this model is owned by the principal identified
    by the given identifier. This is used in read, update or delete operations to determine if
    the given principal can act on this object.

    """

    return self.owner.lower() == str(principal_identifier).lower()


class ExampleViewSet(viewsets.ModelViewSet):
  """
  A viewset that exposes our example model.

  """

  # use our resource owning principal permission class
  permission_classes = [IsResourceOwningPrincipal]


  def get_queryset(self):
    """
    Ensure that the queryset we use is limited based on the conditions we've defined on our model.

    """

    return IsResourceOwningPrincipal.get_queryset_for_principal(Example, self.request)
