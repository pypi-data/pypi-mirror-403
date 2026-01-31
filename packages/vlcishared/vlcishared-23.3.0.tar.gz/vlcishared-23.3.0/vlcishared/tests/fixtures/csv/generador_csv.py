import os
from unittest.mock import MagicMock
import pytest
from vlcishared.csv.generador_csv import GeneradorCSV


@pytest.fixture
def mock_generador_csv_patch(monkeypatch):
    """
    Fixture reutilizable que mockea la clase GeneradorCSV para tests.

    - Mockea los métodos `exportar`, `inicializar_csv` y `escribir_filas_csv`.
    - Ejecuta la lógica real de GeneradorCSV para que se creen los archivos reales.
    - Guarda las rutas generadas en la lista `rutas_csv` para poder hacer asserts.
    - Permite definir side_effect opcionales para cada método.
    
    Uso:
        def test_xxx(mock_generador_csv_patch):
            mock_csv = mock_generador_csv_patch("gestion_csv.gestor_csv.GeneradorCSV", "tests/tmp")
            ruta = mock_csv.exportar("archivo.csv", [["dato1"]], ["col1"])
            assert mock_csv.exportar.call_count == 1
            assert ruta in mock_csv.exportar.rutas_csv
    """
    def _patch(
        ruta_importacion: str,
        carpeta_exportacion: str,
        inicializar_side_effect=None,
        escribir_side_effect=None,
        exportar_side_effect=None,
    ):
        instancia_real = GeneradorCSV(carpeta_exportacion)
        generador_mock = MagicMock(spec=GeneradorCSV)
        rutas_csv = []

        def side_effect_exportar(nombre_fichero, filas, cabecera=None):
            ruta = instancia_real.exportar(nombre_fichero, filas, cabecera)
            rutas_csv.append(ruta)
            if exportar_side_effect:
                return exportar_side_effect(nombre_fichero, filas, cabecera)
            return ruta

        def side_effect_inicializar(nombre_fichero, cabecera=None):
            ruta = instancia_real._construir_ruta(nombre_fichero)
            rutas_csv.append(ruta)
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            instancia_real.inicializar_csv(nombre_fichero, cabecera)
            if inicializar_side_effect:
                return inicializar_side_effect(nombre_fichero, cabecera)
            return ruta

        def side_effect_escribir(ruta, filas):
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            instancia_real.escribir_filas_csv(ruta, filas)
            if escribir_side_effect:
                return escribir_side_effect(ruta, filas)
            return ruta

        generador_mock.exportar.side_effect = side_effect_exportar
        generador_mock.inicializar_csv.side_effect = side_effect_inicializar
        generador_mock.escribir_filas_csv.side_effect = side_effect_escribir

        generador_mock.exportar.rutas_csv = rutas_csv
        generador_mock.inicializar_csv.rutas_csv = rutas_csv

        monkeypatch.setattr(ruta_importacion, lambda *args, **kwargs: generador_mock)
        return generador_mock

    return _patch
