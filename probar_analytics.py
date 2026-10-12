
from app import create_app
from app.services.analytics_service import (
    obtener_indicadores_generales,
    obtener_reportes_por_estado,
    obtener_reportes_por_tipo,
    obtener_reportes_por_mes,
)

app = create_app()

with app.app_context():
    print("\n" + "=" * 50)
    print("PRUEBA DEL SERVICIO ANALÍTICO DE ANIMAL-LIFE")
    print("=" * 50)

    try:
        indicadores = obtener_indicadores_generales()
        print("\n1. INDICADORES GENERALES")
        print(indicadores)

        estados = obtener_reportes_por_estado()
        print("\n2. REPORTES POR ESTADO")
        for registro in estados:
            print(registro)

        tipos = obtener_reportes_por_tipo()
        print("\n3. REPORTES POR TIPO")
        for registro in tipos:
            print(registro)

        meses = obtener_reportes_por_mes()
        print("\n4. REPORTES POR MES")
        for registro in meses:
            print(registro)

        print("\nPRUEBA FINALIZADA CORRECTAMENTE")

    except Exception as error:
        print("\nERROR AL CONSULTAR LA BODEGA DE DATOS")
        print(f"{type(error).__name__}: {error}")
        raise