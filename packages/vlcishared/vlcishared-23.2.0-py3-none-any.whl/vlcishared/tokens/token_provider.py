from vlcishared.http.http import ClienteHTTP


class TokenProvider:
    """
    Clase abstracta encargada de encapsular la lógica genérica para obtener un token vía HTTP POST.

    Parámetros:
        url: URL a la que se enviará la petición para obtener el token.
    """

    def __init__(self, url_token_provider):
        self.url_token_provider = url_token_provider
        self.cliente_http = ClienteHTTP()
        self.token = None

    def _solicitar_nuevo_token(self, *, data=None, files=None):
        """
        Realiza una solicitud POST a la URL configurada con los datos proporcionados.

        Parámetros:
            data (dict, opcional): Datos del formulario.
            files (dict, opcional): Archivos para enviar.

        Retorna:
            dict: La respuesta del servidor como objeto JSON.
        """
        response = self.cliente_http.post(url=self.url_token_provider, data=data, files=files)
        return response

    def obtener_token(self):
        """
        Método abstracto que deben implementar las subclases para establecer self.token.

        Lanza:
            NotImplementedError: Si no se implementa en una subclase.
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
