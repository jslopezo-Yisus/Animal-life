
from sqlalchemy import text
from app.extensions import db


def obtener_indicadores_generales():
    """Obtiene los KPI principales de la bodega de datos."""
    consulta = text("""
        SELECT
            total_reportes,
            reportes_pendientes,
            reportes_resueltos,
            reportes_cerrados,
            usuarios_reportantes
        FROM vw_indicadores_generales
    """)

    with db.engines["dw"].connect() as conexion:
        resultado = conexion.execute(consulta).mappings().first()

        return dict(resultado) if resultado else {}


def obtener_reportes_por_estado():
    """Obtiene la cantidad de reportes agrupados por estado."""
    consulta = text("""
        SELECT estado_id, estado, total_reportes
        FROM vw_reportes_por_estado
        ORDER BY total_reportes DESC
    """)

    with db.engines["dw"].connect() as conexion:
        resultados = conexion.execute(consulta).mappings().all()
        return [dict(fila) for fila in resultados]


def obtener_reportes_por_tipo():
    """Obtiene la cantidad de reportes por tipo."""
    consulta = text("""
        SELECT tipo, total_reportes
        FROM vw_reportes_por_tipo
        ORDER BY total_reportes DESC
    """)

    with db.engines["dw"].connect() as conexion:
        resultados = conexion.execute(consulta).mappings().all()
        return [dict(fila) for fila in resultados]


def obtener_reportes_por_mes():
    """Obtiene la evolución mensual de los reportes."""
    consulta = text("""
        SELECT anio, mes, nombre_mes, total_reportes
        FROM vw_reportes_por_mes
        ORDER BY anio, mes
    """)

    with db.engines["dw"].connect() as conexion:
        resultados = conexion.execute(consulta).mappings().all()
        return [dict(fila) for fila in resultados]