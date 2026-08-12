# src/parser.py
"""
NO necesita lista de municipios.
Detecta automaticamente cual token es el municipio por su comportamiento
(numero vs. palabra), y reconstruye ANCHO, ALTO y PESO cuando vienen pegados.
"""

import re
from src.constantes import COLUMNAS


def es_numero_puro(token):
    """
    True si el token es un numero valido de medida.
    Ejemplos validos: '1' | '1,5' | '0,865' | '72,45'
    Ejemplos invalidos: 'Medellin' | '0,61,895' | '63Medellin' | ''
    """
    if not token or token in (',', '.'):
        return False
    if not re.match(r'^[0-9,.]+$', token):
        return False
    if token.count(',') + token.count('.') > 1:
        return False
    return True


def limpiar_linea(linea):
    """Limpia artefactos comunes del texto extraido de PDF."""
    # Fecha pegada a texto: 14/08/2026INFORME...
    linea = re.sub(r'(\d{2}/\d{2}/\d{4})([A-Za-z])', r'\1 \2', linea)
    # HTML entities
    linea = linea.replace('&#124;', '|')
    return linea


def separar_doble_coma(token):
    """Separa '0,61,895' -> ('0,6', '1,895')."""
    if token.count(',') != 2:
        return None
    for i in range(1, len(token)):
        p1, p2 = token[:i], token[i:]
        if (p1.count(',') == 1 and p2.count(',') == 1 and
            not p1.startswith(',') and not p1.endswith(',') and
            not p2.startswith(',') and not p2.endswith(',')):
            return (p1, p2)
    return None


def separar_entero_decimal(token):
    """Separa '10,815' -> ('1', '0,815') si el entero es 1 digito."""
    if token.count(',') != 1:
        return None
    m = re.match(r'^(\d)(\d+,\d+)$', token)
    if m:
        return (m.group(1), m.group(2))
    return None


def separar_numero_palabra(token):
    """
    Separa '63Medellin' -> ('63', 'Medellin')
    o '4,80Envigado' -> ('4,80', 'Envigado')
    """
    m = re.match(r'^([0-9,]+)([A-Za-z].*)$', token)
    if m:
        num, palabra = m.group(1), m.group(2)
        if es_numero_puro(num):
            return (num, palabra)
    return None


def encontrar_municipio(tokens):
    """
    Encuentra el indice del municipio en la lista de tokens.
    El municipio es el primer token (despues del indice 0) que:
      - Contiene letras, o
      - Es una fecha con slash, o
      - Es una fecha serial larga (5+ digitos antes de la coma)
    """
    tokens_corregidos = list(tokens)

    for i, token in enumerate(tokens):
        if i == 0:
            continue  # CANT siempre es numerico

        # Si tiene letras, es el municipio (o numero pegado a municipio)
        if re.search(r'[A-Za-z]', token):
            sep = separar_numero_palabra(token)
            if sep:
                num, palabra = sep
                tokens_corregidos = (tokens_corregidos[:i] +
                                     [num, palabra] +
                                     tokens_corregidos[i+1:])
                return i + 1, tokens_corregidos
            return i, tokens_corregidos

        # Fecha con slash -> parte de la cola
        if re.match(r'\d{2}/\d{2}/\d{4}', token):
            return i, tokens_corregidos

        # Fecha serial de Excel (5+ digitos, coma, decimales)
        if re.match(r'\d{5,},\d+', token):
            return i, tokens_corregidos

    return len(tokens), tokens_corregidos


def parsear_linea(linea):
    """
    Toma UNA linea de texto del PDF y devuelve un diccionario
    con las 8 columnas. Si la linea no es un pedido valido, devuelve None.
    """
    linea = limpiar_linea(linea)

    # Paso 1: Buscar la O.P (5 digitos al inicio)
    op_match = re.match(r'^(\d{5})\s+', linea)
    if not op_match:
        return None
    op = op_match.group(1)
    resto = linea[op_match.end():]

    # Paso 2: Buscar ITEM + DESCRIPCION
    desc_match = re.search(r'(\d+)(TEMP\s+(?:\w+\s+)*\d+MM)', resto)
    if not desc_match:
        return None

    item = desc_match.group(1)
    desc = desc_match.group(2)
    nombre = resto[:desc_match.start()].strip()
    despues = resto[desc_match.end():].strip()
    tokens = despues.split()

    if len(tokens) < 4:
        return None

    # Paso 3: Encontrar donde esta el municipio
    indice_mun, tokens = encontrar_municipio(tokens)

    # Paso 4: Reconstruir segun la posicion del municipio
    if indice_mun == 4:
        # Caso normal: CANT, ANCHO, ALTO, PESO, MUNICIPIO
        cant = tokens[0]
        ancho = tokens[1]
        alto = tokens[2]
        peso = tokens[3]

    elif indice_mun == 3:
        # Solo 3 tokens numericos antes del municipio
        sep_dc = separar_doble_coma(tokens[1])
        if sep_dc:
            cant = tokens[0]
            ancho, alto = sep_dc
            peso = tokens[2]
        else:
            sep_ed = separar_entero_decimal(tokens[1])
            if sep_ed and es_numero_puro(tokens[2]):
                cant = tokens[0]
                ancho, alto = sep_ed
                peso = tokens[2]
            else:
                cant = tokens[0]
                ancho = tokens[1]
                alto = tokens[2]
                peso = ""

    elif indice_mun == 2:
        cant = tokens[0]
        ancho = tokens[1]
        alto = ""
        peso = ""

    else:
        cant = tokens[0] if len(tokens) > 0 else ""
        ancho = tokens[1] if len(tokens) > 1 else ""
        alto = tokens[2] if len(tokens) > 2 else ""
        peso = tokens[3] if len(tokens) > 3 else ""

    return {
        'O.P': op,
        'RAZON SOCIAL': nombre,
        'ITEM': item,
        'DESCRIPCION': desc,
        'CANT': cant,
        'ANCHO': ancho,
        'ALTO': alto,
        'PESO': peso
    }


def parsear_paginas(lista_paginas):
    """
    Toma una lista de paginas (texto) y devuelve una lista de diccionarios.
    """
    filas = []
    for pagina in lista_paginas:
        for linea in pagina.strip().split('\n'):
            fila = parsear_linea(linea)
            if fila:
                filas.append(fila)
    return filas