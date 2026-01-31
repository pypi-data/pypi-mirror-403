from abc import ABC
from vlcishared.tokens.arcgis_token_provider_config import ArcGISTokenProviderConfig
from vlcishared.tokens.token_provider import TokenProvider


class ArcGISTokenProvider(TokenProvider, ABC):
    """
    Clase base abstracta para proveedores de tokens de ArcGIS.
    Define la estructura y delega en las subclases la generación
    del payload concreto.
    """

    def __init__(self, config: ArcGISTokenProviderConfig):
        super().__init__(config.url_token_provider)
        self.username = config.username
        self.password = config.password
        self.format = config.format
        self.client = config.client
        self.expiration = config.expiration

    def obtener_token(self):
        """
        Realiza la solicitud del token al servidor ArcGIS usando las credenciales
        y parámetros configurados. Asigna el token recibido a self.token.

        Lanza:
            ValueError: Si la respuesta no contiene un token válido.

        Devuelve:
            Token obtenido
        """
        payload = self.get_payload()
        respuesta = self._solicitar_nuevo_token(data=payload)
        token = respuesta.get("token")
        if token is None:
            raise ValueError("No se ha podido obtener el token.")
        self.token = token
        
        return token

    def get_payload(self):
        """
        Generación del payload específico de la solicitud de token.
        """
        return {
            "username": self.username,
            "password": self.password,
            "f": self.format,
            "client": self.client,
            "expiration": self.expiration,
        }