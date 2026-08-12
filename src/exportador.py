# src/exportador.py
import pandas as pd
from pathlib import Path
from src.constantes import COLUMNAS


def guardar_excel(datos, ruta_salida, nombre_hoja="Pedidos"):
    """
    Guarda una lista de diccionarios en un archivo Excel.
    """
    df = pd.DataFrame(datos, columns=COLUMNAS)
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(str(ruta), index=False, sheet_name=nombre_hoja)
    return len(datos)