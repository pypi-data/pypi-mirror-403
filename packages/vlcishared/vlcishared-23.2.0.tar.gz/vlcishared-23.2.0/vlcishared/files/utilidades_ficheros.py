import os
import re
import zipfile
from datetime import datetime

from vlcishared.excepciones.excepciones import ExtensionFicheroInvalidaError


def ordenar_ficheros_por_fecha_en_nombre(formato_fecha, ficheros):
    """
    Ordena una lista de nombres de ficheros según la fecha contenida en su nombre.

    Args:
        formato_fecha (str): Formato en el que está escrita la fecha en el nombre del fichero (por ejemplo: '%Y%m%d', '%Y_%m_%d').
        ficheros (list of str): Lista de nombres de ficheros a ordenar.

    Returns:
        list of str: Lista de nombres de ficheros ordenados cronológicamente según la fecha extraída.
    """
    archivos_con_fecha = []
    for fichero in ficheros:
        fecha = extraer_fecha_desde_nombre_fichero(formato_fecha, fichero)
        archivos_con_fecha.append((fecha, fichero))

    archivos_con_fecha.sort(key=lambda x: x[0])
    return [nombre for _, nombre in archivos_con_fecha]


def extraer_fecha_desde_nombre_fichero(formato_fecha, nombre_fichero):
    """
    Extrae la fecha del nombre de un fichero usando un patrón regex y un formato específico.

    Args:
        formato_fecha (str): Formato en el que está escrita la fecha en el nombre del fichero (por ejemplo: '%Y%m%d', '%Y_%m_%d').
        nombre_fichero (str): Nombre del fichero del que extraer la fecha.

    Returns:
        datetime: Objeto datetime con la fecha extraída.

    Raises:
        ValueError: Si no se encuentra una fecha válida en el nombre del fichero o el formato no coincide.
    """
    patron_fecha_str = formato_a_patron_regex(formato_fecha)
    patron_fecha_compilado = re.compile(patron_fecha_str)
    match = patron_fecha_compilado.search(nombre_fichero)
    if not match:
        raise ValueError(f"El fichero {nombre_fichero} no contiene una fecha válida")

    fecha_str = match.group(0)
    return datetime.strptime(fecha_str, formato_fecha)


def formato_a_patron_regex(formato_fecha: str) -> str:
    r"""
    Convierte un formato de fecha de datetime a un patrón regex.

    Args:
        formato_fecha (str): como '%Y_%m_%d' o '%d-%m-%Y'

    Returns:
        str: patrón regex equivalente, ej: r"\d{4}_\d{2}_\d{2}"
    """
    mapping = {
        "%Y": r"\d{4}",
        "%y": r"\d{2}",
        "%m": r"\d{2}",
        "%d": r"\d{2}",
    }

    patron = formato_fecha
    for token, regex_equivalente in mapping.items():
        patron = patron.replace(token, regex_equivalente)

    patron = re.sub(r"(?<!\\)([^\w\\{}])", r"\\\1", patron)
    return patron


def comprimir_fichero_en_zip(ruta_fichero: str) -> str:
    """
    Comprime un fichero cualquiera en un archivo ZIP en la misma carpeta.

    Args:
        ruta_fichero (str): Ruta completa del fichero que se desea comprimir.

    Returns:
        str: Ruta completa del archivo ZIP creado que contiene el fichero original.
    """
    nombre_base = os.path.splitext(os.path.basename(ruta_fichero))[0]

    ruta_zip = os.path.join(os.path.dirname(ruta_fichero), f"{nombre_base}.zip")

    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(ruta_fichero, arcname=os.path.basename(ruta_fichero))

    return ruta_zip


def validar_extension_fichero(nombre_fichero: str, extension_esperada: str):
    """
    Valida que un fichero tiene la extensión esperada.

    Args:
        nombre_fichero (str): Nombre del fichero a validar.
        extension_esperada (str): Extensión esperada (con o sin el punto inicial).

    Raises:
        ValueError: Si la extensión del fichero no coincide con la esperada.
    """
    _, extension = os.path.splitext(nombre_fichero)
    extension = extension.lstrip(".")
    extension_esperada = extension_esperada.lstrip(".")

    if extension.lower() != extension_esperada.lower():
        raise ExtensionFicheroInvalidaError(f"El fichero {nombre_fichero} no tiene la extensión esperada: {extension_esperada}")


def extraer_propiedad_linea_fichero_strip(linea: str, intervalo_caracteres: str) -> str:
    return _extraer_subcadena(linea, intervalo_caracteres).strip()


def extraer_propiedad_linea_fichero_rstrip(linea: str, intervalo_caracteres: str) -> str:
    return _extraer_subcadena(linea, intervalo_caracteres).rstrip()


def extraer_propiedad_linea_fichero_lstrip(linea: str, intervalo_caracteres: str) -> str:
    return _extraer_subcadena(linea, intervalo_caracteres).lstrip()


def _extraer_subcadena(linea: str, intervalo_caracteres: str) -> str:
    """
    Extrae una subcadena de una línea en base a un intervalo de posiciones.

    El intervalo se recibe como una cadena con dos números separados por caracteres no numéricos,
    por ejemplo: "5-10" o "5,10". Estos valores indican las posiciones inicial y final dentro de la línea.

    Args:
        linea (str): Línea completa de la que se extraerá la subcadena.
        intervalo_caracteres (str): Intervalo con el formato "<inicio><separador><fin>",
            donde inicio y fin son índices enteros.

    Returns:
        str: Subcadena recortada.

    Raises:
        ValueError: Si el formato del intervalo no es válido.
    """
    match = re.match(r"(\d+)\D+(\d+)", intervalo_caracteres)
    if not match:
        raise ValueError(f"Formato de intervalo inválido: {intervalo_caracteres}")

    inicio, fin = map(int, match.groups())
    return linea[inicio:fin]
