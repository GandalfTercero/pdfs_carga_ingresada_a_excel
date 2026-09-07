"""
Tests automaticos para el parser.
Correlos con: python -m pytest tests/
"""

from src.parser import parsear_linea, es_numero_puro


def test_linea_normal():
    linea = "16928 ALUMINIO S.A.S 1TEMP INCOL 8MM 1 1,5 2,415 72,45"
    r = parsear_linea(linea)
    assert r is not None
    assert r['O.P'] == '16928'
    assert r['RAZON SOCIAL'] == 'ALUMINIO S.A.S'
    assert r['ITEM'] == '1'
    assert r['DESCRIPCION'] == 'TEMP INCOL 8MM'
    assert r['CANT'] == '1'
    assert r['ANCHO'] == '1,5'
    assert r['ALTO'] == '2,415'
    assert r['PESO'] == '72,45'


def test_item_pegado():
    linea = "16909 ANDREA TAMAYO GIL1 TEMP INCOL 8MM 1 1,05 0,95 19,95"
    r = parsear_linea(linea)
    assert r['RAZON SOCIAL'] == 'ANDREA TAMAYO GIL'
    assert r['ITEM'] == '1'


def test_doble_coma():
    linea = "17261 CLIENTE 10TEMP INCOL 10MM 1 0,61,895 26,77"
    r = parsear_linea(linea)
    assert r['ANCHO'] == '0,6'
    assert r['ALTO'] == '1,895'
    assert r['PESO'] == '26,77'


def test_entero_decimal():
    linea = "18023 DANIEL VELEZ GIRALDO 3TEMP INCOL 6MM 2 12,14 64,20"
    r = parsear_linea(linea)
    assert r['ANCHO'] == '1'
    assert r['ALTO'] == '2,14'
    assert r['PESO'] == '64,20'


def test_peso_pegado_municipio():
    linea = "17959 YAMILE LOPEZ 6TEMP INCOL 10MM 1 1,2 2,1 63Medellin"
    r = parsear_linea(linea)
    assert r['PESO'] == '63'


def test_municipio_nuevo():
    """El parser debe funcionar con municipios que nunca ha visto."""
    linea = "99999 CLIENTE NUEVO 1TEMP INCOL 8MM 1 1,0 2,0 20,0 Cali"
    r = parsear_linea(linea)
    assert r is not None
    assert r['PESO'] == '20,0'


def test_es_numero_puro():
    assert es_numero_puro('72,45') is True
    assert es_numero_puro('1') is True
    assert es_numero_puro('0,61,895') is False
    assert es_numero_puro('63Medellin') is False
    assert es_numero_puro('Medellin') is False

def test_item_vacio():
    """Maneja ITEM vacio (dos pipes seguidos en la tabla del PDF)."""
    linea = "18452 ALUMINIOS AJR S.A.S TEMP INCOL 8MM 4 1,076 2,795 240,59 Medellin 14/08/2026 20/08/2026"
    r = parsear_linea(linea)
    assert r is not None
    assert r['O.P'] == '18452'
    assert r['DESCRIPCION'] == 'TEMP INCOL 8MM'


def test_fechas_extraidas():
    """Extrae FECHA_O_P y FECHA_SOL_DESPACHO."""
    linea = "18447 ALUMINIO S.A.S 1TEMP INCOL 5MM 2 1,06 0,665 17,62 Medellin 14/08/2026 20/08/2026"
    r = parsear_linea(linea)
    assert r['FECHA_O_P'] == '14/08/2026'
    assert r['FECHA_SOL_DESPACHO'] == '20/08/2026'


def test_fecha_serial():
    """Convierte fecha serial de Excel a formato legible."""
    linea = "18424 CLIENTE 1TEMP INCOL 6MM 1 0,76 0,74 8,40 Medellin 46247,72568 46254"
    r = parsear_linea(linea)
    assert r['FECHA_O_P'] == '13/08/2026'
    assert r['FECHA_SOL_DESPACHO'] == '20/08/2026'


def test_limpieza_nombre_cliente():
    """Separa nombres pegados como ALUMINIOSAJR."""
    linea = "18447 ALUMINIOSAJR S.A.S 1TEMP INCOL 5MM 2 1,06 0,665 17,62 Medellin 14/08/2026 20/08/2026"
    r = parsear_linea(linea)
    assert r['RAZON SOCIAL'] == 'ALUMINIOS AJR S.A.S'


def test_normalizacion_descripcion():
    """Corrige 10M a 10MM."""
    linea = "18452 CLIENTE 5TEMP INCOL 10M 2 1,451 2,845 206,40 Medellin 14/08/2026 20/08/2026"
    r = parsear_linea(linea)
    assert r['DESCRIPCION'] == 'TEMP INCOL 10MM'