# src/exportador.py
import pandas as pd
from pathlib import Path
from src.constantes import COLUMNAS


def _a_float(valor):
    """Convierte string con coma decimal a float. Si falla, devuelve None."""
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace('.', ',').replace(',', '.'))
    except (ValueError, TypeError):
        return None


def guardar_excel(datos, ruta_salida, nombre_hoja="Pedidos", log=None):
    """
    Guarda una lista de diccionarios en un archivo Excel.
    Convierte campos numericos a float, elimina duplicados y genera log.
    """
    if not datos:
        return 0

    df = pd.DataFrame(datos, columns=COLUMNAS)

    # Convertir numericos a float
    for col in ['CANT', 'ANCHO', 'ALTO', 'PESO']:
        df[col] = df[col].apply(_a_float)

    # Eliminar duplicados por O.P + ITEM (conservar el primero)
    antes = len(df)
    df = df.drop_duplicates(subset=['O.P', 'ITEM'], keep='first')
    duplicados_eliminados = antes - len(df)

    # Generar reporte de log
    if log:
        ruta_log = Path(ruta_salida).with_suffix('.log.txt')
        ignoradas = [e for e in log if e['tipo'] == 'ignorada']
        sospechosas = [e for e in log if e['tipo'] == 'sospechoso']

        with open(ruta_log, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("  REPORTE DE PROCESAMIENTO DE PDF\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Filas extraidas del PDF:     {antes}\n")
            f.write(f"Duplicados eliminados:       {duplicados_eliminados}\n")
            f.write(f"Filas finales en Excel:      {len(df)}\n")
            f.write(f"Lineas ignoradas:            {len(ignoradas)}\n")
            f.write(f"Lineas con datos sospechosos: {len(sospechosas)}\n\n")

            if sospechosas:
                f.write("-" * 60 + "\n")
                f.write("LINEAS CON CAMPOS VACIOS O SOSPECHOSOS\n")
                f.write("-" * 60 + "\n")
                for e in sospechosas:
                    f.write(f"\n[{e['op']} - Item {e['item']}]\n")
                    f.write(f"  Motivo: {e['detalle']}\n")
                    f.write(f"  Texto:  {e['linea'][:120]}\n")

            if ignoradas:
                f.write("\n" + "-" * 60 + "\n")
                f.write("LINEAS IGNORADAS (NO COINCIDIERON CON EL PATRON)\n")
                f.write("-" * 60 + "\n")
                for e in ignoradas:
                    f.write(f"\n  {e['linea'][:120]}\n")

        print(f"  Log generado: {ruta_log}")

    # Guardar Excel
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(str(ruta), index=False, sheet_name=nombre_hoja)
    return len(df)