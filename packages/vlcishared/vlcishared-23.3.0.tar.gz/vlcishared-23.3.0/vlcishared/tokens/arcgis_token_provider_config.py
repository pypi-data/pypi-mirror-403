class ArcGISTokenProviderConfig:
    """
    Configuración para el proveedor de tokens de ArcGIS Geoportal.
    """

    def __init__(self, url_token_provider, username, password, format, client, expiration):
        self.url_token_provider = url_token_provider
        self.username = username
        self.password = password
        self.format = format
        self.client = client
        self.expiration = expiration