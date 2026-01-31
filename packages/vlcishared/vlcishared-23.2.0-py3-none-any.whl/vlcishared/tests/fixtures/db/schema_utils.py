import pandas as pd
from sqlalchemy import text, MetaData, Table, Column
from sqlalchemy.types import Float, String, DateTime


def copiar_tablas(connection, esquema_origen, esquema_destino):
    """
    Copia todas las tablas del esquema original al de test. Se ejecuta una vez por sesión.
    Usa la misma conexión que el resto de los tests.
    """
    tablas = (
        connection.execute(
            text(
                """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :esquema
            """
            ),
            {"esquema": esquema_origen},
        )
        .scalars()
        .all()
    )

    for tabla in tablas:
        connection.execute(
            text(
                f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_tables WHERE tablename = '{tabla}' AND schemaname = '{esquema_destino}'
                ) THEN
                    EXECUTE 'CREATE TABLE {esquema_destino}.{tabla} (LIKE {esquema_origen}.{tabla} INCLUDING ALL)';
                END IF;
            END
            $$;
        """
            )
        )

    connection.commit()


def copiar_funciones_y_procedimientos(connection, esquema_origen, esquema_destino):

    funciones = (
        connection.execute(
            text(
                """
            SELECT p.oid
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = :esquema
            """
            ),
            {"esquema": esquema_origen},
        )
        .scalars()
        .all()
    )

    for oid in funciones:
        definicion = connection.execute(text("SELECT pg_get_functiondef(:oid)"), {"oid": oid}).scalar()

        if not definicion:
            continue

        definicion = definicion.replace(f"{esquema_origen}.", f"{esquema_destino}.")

        try:
            connection.execute(text(definicion))
        except Exception as e:
            print(f"Error creando función/procedimiento {oid}: {e}")

    connection.commit()


def borrar_tablas(connection, esquema):
    tablas = (
        connection.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = :esquema
                """
            ),
            {"esquema": esquema},
        )
        .scalars()
        .all()
    )
    for tabla in tablas:
        connection.execute(text(f"DROP TABLE IF EXISTS {esquema}.{tabla} CASCADE"))
    connection.commit()


def borrar_funciones_y_procedimientos(connection, esquema):
    funciones = connection.execute(
        text(
            """
            SELECT
                p.proname,
                pg_get_function_identity_arguments(p.oid) AS args,
                p.prokind
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = :esquema
            """
        ),
        {"esquema": esquema},
    ).fetchall()

    for nombre, args, tipo in funciones:
        drop_type = "PROCEDURE" if tipo == "p" else "FUNCTION"
        try:
            connection.execute(text(f'DROP {drop_type} IF EXISTS {esquema}."{nombre}"({args}) CASCADE'))
        except Exception as e:
            print(f"Error borrando {drop_type.lower()} {nombre}({args}): {e}")
            connection.rollback()

    connection.commit()


TYPE_MAP_ORACLE = {
    "NUMBER": Float,
    "FLOAT": Float,
    "VARCHAR2": String,
    "CHAR": String,
    "NVARCHAR2": String,
    "DATE": DateTime,
    "TIMESTAMP": DateTime,
}


def copiar_tabla_oracle_a_sqlite(oracle_conn, sqlite_conn, tabla: str, esquema_origen: str, copiar_datos=True):
    columnas = oracle_conn.execute_query(
        f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM ALL_TAB_COLUMNS
        WHERE TABLE_NAME = '{tabla.upper()}'
          AND OWNER = '{esquema_origen.upper()}'
        ORDER BY COLUMN_ID
        """
    ).fetchall()

    pks = oracle_conn.execute_query(
        f"""
        SELECT cols.COLUMN_NAME
        FROM ALL_CONSTRAINTS cons
        JOIN ALL_CONS_COLUMNS cols
          ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
        WHERE cons.TABLE_NAME = '{tabla.upper()}'
          AND cons.OWNER = '{esquema_origen.upper()}'
          AND cons.CONSTRAINT_TYPE = 'P'
        ORDER BY cols.POSITION
        """
    ).fetchall()

    pk_cols = [pk[0] for pk in pks] if pks else []

    metadata = MetaData()
    cols = [Column(c[0], TYPE_MAP_ORACLE.get(c[1].upper(), String), primary_key=(c[0] in pk_cols)) for c in columnas]

    nueva_tabla = Table(tabla, metadata, *cols)
    metadata.create_all(sqlite_conn)

    if copiar_datos:
        df = pd.read_sql(f"SELECT * FROM {esquema_origen}.{tabla}", oracle_conn.engine)
        df.to_sql(tabla, sqlite_conn, if_exists="append", index=False)


def copiar_estructura_vista_oracle_a_sqlite(oracle_conn, sqlite_conn, vista: str, esquema_origen: str):
    """
    Crea en SQLite una vista o tabla vacía con la misma estructura de columnas que la vista Oracle.
    No copia datos ni el SQL completo.
    """
    columnas = oracle_conn.execute_query(
        f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM ALL_TAB_COLUMNS
        WHERE TABLE_NAME = '{vista.upper()}'
          AND OWNER = '{esquema_origen.upper()}'
        ORDER BY COLUMN_ID
    """
    ).fetchall()

    if not columnas:
        raise ValueError(f"No se encontró la vista {esquema_origen}.{vista}")

    metadata = MetaData()
    cols = [Column(c[0], TYPE_MAP_ORACLE.get(c[1].upper(), String)) for c in columnas]

    Table(vista, metadata, *cols)
    metadata.create_all(sqlite_conn)
