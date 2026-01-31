import sqlite3
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from vlcishared.db.oracle import OracleConnector
from vlcishared.tests.fixtures.db.schema_utils import copiar_tabla_oracle_a_sqlite, copiar_estructura_vista_oracle_a_sqlite


@pytest.fixture
def mock_oracle_patch(monkeypatch, db_transaction):
    """
    Fixture que mockea OracleConnector para ejecutar queries sobre una base de datos real (SQLite de prueba).

    - Redirige métodos como connect, execute y execute_query al engine de pruebas.
    - Permite testear sin conectarse a una base de datos real de producción.
    - Requiere la ruta del import de OracleConnector.

    Parámetros:
    - ruta_importacion (str): Ruta completa donde se importa `PostgresConnector` (ej. "mi_paquete.mi_modulo.PostgresConnector").
    - execute_query_side_effect (callable|None): Lógica personalizada a ejecutar cuando se llama `execute_query`.
    - execute_many_side_effect (callable|None): Lógica personalizada a ejecutar cuando se llama `execute_many`.
    - insert_many_rows_side_effect (callable|None): Lógica personalizada a ejecutar cuando se llama `insert_many_rows`.
    - call_function_side_effect (callable|None): Lógica personalizada a ejecutar cuando se llama `call_function`.
    - call_procedure_side_effect (callable|None): Lógica personalizada a ejecutar cuando se llama `call_procedure`.

    Uso:
        def test_xxx(mock_db_patch):
            mock_db = mock_db_patch("modulo.donde.importa.PostgresConnector")
            mock_db.execute.assert_called_once()

        def test_execute_query(mock_oracle_patch):
            mock_oracle = mock_oracle_patch(
                "modulo.OracleConnector",
                execute_query_return=[{"columna": "valor"}]
            )
            resultado = mock_oracle.execute_query()
            assert resultado[0]._mapping["columna"] == "valor"
    """

    def _patch(
        ruta_importacion: str,
        execute_query_return=None,
        execute_query_side_effect=None,
        execute_many_query_return=None,
        execute_many_query_side_effect=None,
        insert_many_rows_side_effect=None,
        call_function_side_effect=None,
        call_function_return=None,
        call_procedure_side_effect=None,
        call_procedure_return=None,
    ):
        mock_connector = MagicMock()

        mock_connector.connect.return_value = db_transaction
        mock_connector.close.return_value = None
        mock_connector.commit.side_effect = lambda: db_transaction.commit()
        mock_connector.rollback.side_effect = lambda: db_transaction.rollback()

        if execute_query_return is not None:
            mock_connector.execute_query.return_value = execute_query_return_mappings(execute_query_return)
        else:
            mock_connector.execute_query.side_effect = execute_query_side_effect or execute_query_side_effect_default(db_transaction)

        if execute_many_query_return is not None:
            mock_connector.execute_many_query.return_value = execute_query_return_mappings(execute_many_query_return)
        else:
            mock_connector.execute_many_query.side_effect = execute_many_query_side_effect or execute_many_side_effect_default(db_transaction)

        mock_connector.insert_many_rows.side_effect = insert_many_rows_side_effect or insert_many_rows_side_effect_default(db_transaction)

        if call_procedure_return is not None:
            mock_connector.call_procedure.return_value = execute_query_return_mappings(call_procedure_return)
        else:
            mock_connector.call_procedure.side_effect = call_procedure_side_effect or None

        if call_function_return is not None:
            mock_connector.call_function.return_value = call_function_return
        else:
            mock_connector.call_function.side_effect = call_function_side_effect

        monkeypatch.setattr(ruta_importacion, lambda *args, **kwargs: mock_connector)
        return mock_connector

    yield _patch


@pytest.fixture
def db_transaction(connection):
    transaction = connection.begin_nested()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()


@pytest.fixture(scope="session")
def connection():
    """
    Crea una conexión de SQLAlchemy contra una base de datos sqlite de prueba.
    - Devuelve una conexión viva que se cierra al finalizar el test.
    - Usado por otros fixtures para ejecutar queries reales en un entorno aislado.
    """
    engine = create_engine("sqlite:///:memory:", isolation_level="SERIALIZABLE", connect_args={"detect_types": sqlite3.PARSE_DECLTYPES})
    connection = engine.connect()
    yield connection
    connection.close()
    engine.dispose()


@pytest.fixture(scope="session")
def setup_esquema_test_desde_oracle(connection):
    def _copiar_esquema(oracle_conn: OracleConnector, esquema_origen: str, tablas: list[str], vistas: list[str], copiar_datos: bool = True):
        oracle_conn.connect()
        copiar_esquema(connection, oracle_conn, esquema_origen, tablas, vistas, copiar_datos)

    yield _copiar_esquema


def copiar_esquema(connection, oracle_conn, esquema_origen, tablas, vistas, copiar_datos):
    """
    Copia tablas y funciones/procedimientos del esquema origen al destino.
    """
    if tablas:
        for t in tablas:
            copiar_tabla_oracle_a_sqlite(oracle_conn, connection, t, esquema_origen, copiar_datos)

    if vistas:
        for v in vistas:
            copiar_estructura_vista_oracle_a_sqlite(oracle_conn, connection, v, esquema_origen)


def execute_query_return_mappings(return_value: dict):
    rows = []
    for row_dict in return_value:
        row_mock = MagicMock()
        row_mock._mapping = row_dict
        rows.append(row_mock)
    return rows


def execute_query_side_effect_default(conn):
    def _execute(query, *params):
        query_obj = text(query)
        result = conn.execute(query_obj, params or {})
        return result.mappings().all() if result.returns_rows else result

    return with_rollback(conn, _execute)


def execute_many_side_effect_default(conn):
    def _execute(query, params_list):
        conn.execute(text(query), params_list)

    return with_rollback(conn, _execute)


def insert_many_rows_side_effect_default(conn):
    def _execute(query, df):
        if not df.empty:
            params_list = df.to_dict(orient="records")
            query_obj = text(query) if isinstance(query, str) else query
            conn.execute(query_obj, params_list)

    return with_rollback(conn, _execute)


def with_rollback(conn, func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            conn.rollback()
            raise

    return wrapper
