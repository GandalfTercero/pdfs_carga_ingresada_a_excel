"""
PDF Pedidos -> Excel
==================
Convierte automaticamente los PDFs de pedidos a archivos Excel.

Uso:
    python main.py
    python main.py --consolidar
"""

import argparse
from pathlib import Path
from src.extractor import extraer_texto_pdf
from src.parser import parsear_paginas
from src.exportador import guardar_excel


def procesar_pdf(ruta_pdf, carpeta_salida):
    """PDF -> texto -> datos -> Excel."""
    print(f"Procesando: {ruta_pdf.name}")

    paginas = extraer_texto_pdf(ruta_pdf)
    datos = parsear_paginas(paginas)

    if not datos:
        print(f"  No se encontraron datos en {ruta_pdf.name}")
        return 0

    nombre_salida = carpeta_salida / f"{ruta_pdf.stem}.xlsx"
    total_filas = guardar_excel(datos, nombre_salida)

    print(f"  {total_filas} filas -> {nombre_salida.name}")
    return total_filas


def main():
    parser = argparse.ArgumentParser(
        description="Convierte PDFs de pedidos a Excel."
    )
    parser.add_argument('--consolidar', action='store_true',
                        help='Genera un solo Excel con todos los PDFs')
    parser.add_argument('--prefijo', default='',
                        help='Prefijo para los nombres de archivo de salida')
    args = parser.parse_args()

    carpeta_pdfs = Path("pdfs")
    carpeta_excels = Path("excels")

    if not carpeta_pdfs.exists():
        print(f"Error: No existe la carpeta '{carpeta_pdfs}'")
        print("Crea la carpeta y pon tus PDFs adentro.")
        return

    carpeta_excels.mkdir(exist_ok=True)

    archivos_pdf = sorted(carpeta_pdfs.glob("*.pdf"))
    if not archivos_pdf:
        print(f"No se encontraron PDFs en '{carpeta_pdfs}'")
        return

    print(f"{len(archivos_pdf)} PDF(s) encontrado(s)\n")

    todos_los_datos = []
    total_general = 0

    for pdf in archivos_pdf:
        if args.consolidar:
            paginas = extraer_texto_pdf(pdf)
            datos = parsear_paginas(paginas)
            todos_los_datos.extend(datos)
            total_general += len(datos)
            print(f"  {pdf.name}: {len(datos)} filas")
        else:
            total_general += procesar_pdf(pdf, carpeta_excels)

    if args.consolidar and todos_los_datos:
        nombre_consolidado = carpeta_excels / f"{args.prefijo}CONSOLIDADO.xlsx"
        n_total = guardar_excel(todos_los_datos, nombre_consolidado)
        print(f"\nConsolidado: {n_total} filas totales -> {nombre_consolidado.name}")

    print("\n" + "-" * 50)
    print(f"Listo. Total de filas procesadas: {total_general}")


if __name__ == "__main__":
    main()