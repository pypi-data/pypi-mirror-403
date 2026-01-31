import csv
import os
from typing import List, Optional


class GeneradorCSV:
    def __init__(self, carpeta_exportacion: str, delimitador: str = ";"):
        self._carpeta_exportacion = carpeta_exportacion
        self._delimitador = delimitador

    def exportar(self, nombre_fichero: str, filas: List[List], cabecera: Optional[List[str]] = None) -> str:
        """
        Exporta los datos a un archivo CSV en la carpeta de exportación.

        Args:
            nombre_fichero (str): Nombre del fichero, ej. 'datos.csv'.
            filas (List[List]): Lista de listas con las filas del CSV.
            cabecera (Optional[List[str]]): Cabecera del CSV, si se desea incluir.

        Returns:
            str: Ruta absoluta del fichero generado.
        """
        ruta_csv = self.inicializar_csv(nombre_fichero, cabecera)
        self.escribir_filas_csv(ruta_csv, filas)
        return ruta_csv

    def inicializar_csv(self, nombre_fichero: str, cabecera: Optional[List[str]] = None) -> str:
        """
        Crea un fichero CSV vacío (solo cabecera, si se indica).
        Devuelve la ruta completa del fichero.
        """
        os.makedirs(self._carpeta_exportacion, exist_ok=True)
        ruta_csv = self._construir_ruta(nombre_fichero)
        os.makedirs(self._carpeta_exportacion, exist_ok=True)
        with open(ruta_csv, mode="w", newline="", encoding="utf-8") as fichero_csv:
            writer = csv.writer(fichero_csv, delimiter=self._delimitador)
            if cabecera:
                writer.writerow(cabecera)
        return ruta_csv

    def escribir_filas_csv(self, ruta_csv: str, filas: List[List]) -> None:
        """
        Añade un lote de filas al CSV existente, sin sobrescribir el contenido.
        """
        if not filas:
            return
        with open(ruta_csv, mode="a", newline="", encoding="utf-8") as fichero_csv:
            writer = csv.writer(fichero_csv, delimiter=self._delimitador)
            writer.writerows(filas)

    def _construir_ruta(self, nombre_fichero: str) -> str:
        """Crea la carpeta si no existe y devuelve la ruta completa del archivo."""
        os.makedirs(self._carpeta_exportacion, exist_ok=True)
        ruta_exportacion = os.path.join(self._carpeta_exportacion, nombre_fichero)
        return ruta_exportacion
