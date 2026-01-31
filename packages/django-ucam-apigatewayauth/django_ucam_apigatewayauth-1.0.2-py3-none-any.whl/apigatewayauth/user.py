from dataclasses import dataclass
from typing import Optional, Set

from django.contrib.auth.models import AnonymousUser
from identitylib.identifiers import Identifier


@dataclass(eq=True)
class APIGatewayAuthenticationDetails:
    """
    A dataclass representing the authentication information passed from the API Gateway.

    """

    principal_identifier: Identifier
    scopes: Set[str]
    app_id: Optional[str] = None
    client_id: Optional[str] = None


class APIGatewayUser(AnonymousUser):
    """
    A Django user representing the authenticated principal. This user is not
    backed by a database object and so they can have no permissions in the
    Django sense.
    """

    def __init__(self, auth: APIGatewayAuthenticationDetails):
        super().__init__()
        self.username = self.id = self.pk = str(auth.principal_identifier)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.username
