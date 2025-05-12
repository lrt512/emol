from authlib.integrations.django_client import OAuth


class GoogleOAuth(OAuth):
    """
    Subclass authlib.OAuth for Google SSO
    """

    CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"

    def __init__(self):
        super().__init__()
        self.register(
            name="google",
            server_metadata_url=self.CONF_URL,
            client_kwargs={"scope": "openid email profile"},
        )
