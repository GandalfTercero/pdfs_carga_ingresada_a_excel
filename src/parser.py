# src/parser.py
"""
NO necesita lista de municipios.
Detecta automaticamente cual token es el municipio por su comportamiento
(numero vs. palabra), y reconstruye ANCHO, ALTO y PESO cuando vienen pegados.
"""

import re
from src.constantes import COLUMNAS


# Diccionario de correcciones de nombres conocidos (ampliar segun necesites)
_CORRECCIONES_NOMBRE = {
    "ALUMINIOSAJR": "ALUMINIOS AJR",
    "CORVITMEDELLIN": "CORVIT MEDELLIN",
    "ENTREVIDRIOSLA30": "ENTREVIDRIOS LA 30",
}

# Correcciones de descripcion
_CORRECCIONES_DESC = {
    "10M": "10MM",
    "8M": "8MM",
    "6M": "6MM",
    "5M": "5MM",
    "4M": "4MM",
}


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


def _convertir_fecha_serial(token):
    """Convierte fecha serial de Excel (ej: 46248,41547) a dd/mm/yyyy."""
    try:
        import datetime
        numero = float(token.replace(',', '.'))
        base = datetime.datetime(1899, 12, 30)
        fecha = base + datetime.timedelta(days=numero)
        return fecha.strftime('%d/%m/%Y')
    except Exception:
        return token


def _limpiar_nombre_cliente(nombre):
    """Aplica correcciones conocidas y separa S.A.S / S.A. / LTDA."""
    # Correcciones especificas del diccionario
    for mal, bien in _CORRECCIONES_NOMBRE.items():
        nombre = nombre.replace(mal, bien)

    # Separar extensiones juridicas pegadas
    nombre = re.sub(r'([A-Za-z])(S\.A\.S)', r'\1 \2', nombre)
    nombre = re.sub(r'([A-Za-z])(S\.A\.)', r'\1 \2', nombre)
    nombre = re.sub(r'([A-Za-z])(LTDA)', r'\1 \2', nombre)
    return nombre.strip()


def _limpiar_descripcion(desc):
    """Normaliza typos de espesor (10M -> 10MM)."""
    for mal, bien in _CORRECCIONES_DESC.items():
        desc = desc.replace(mal, bien)
    return desc


def encontrar_municipio(tokens):
    """
    Encuentra el indice del municipio en la lista de tokens.
    El municipio es el primer token (despues del indice 0) que:
      - Contiene letras, o
      - Es una fecha con slash, o
      - Es una fecha serial larga (5+ digitos antes de la coma)
    Devuelve: (indice_mun, tokens_corregidos, fechas_encontradas)
    """
    tokens_corregidos = list(tokens)
    fechas = []

    for i, token in enumerate(tokens):
        if i == 0:
            continue  # CANT siempre es numerico

        # Fecha con slash -> la guardamos y seguimos (puede haber dos)
        if re.match(r'\d{2}/\d{2}/\d{4}', token):
            fechas.append(token)
            continue

        # Fecha serial de Excel (5+ digitos, coma, decimales)
        if re.match(r'\d{5,},\d+', token):
            fechas.append(_convertir_fecha_serial(token))
            continue

        # Si tiene letras, es el municipio (o numero pegado a municipio)
        if re.search(r'[A-Za-z]', token):
            sep = separar_numero_palabra(token)
            if sep:
                num, palabra = sep
                tokens_corregidos = (tokens_corregidos[:i] +
                                     [num, palabra] +
                                     tokens_corregidos[i+1:])
                return i + 1, tokens_corregidos, fechas
            return i, tokens_corregidos, fechas

    return len(tokens), tokens_corregidos, fechas


def parsear_linea(linea):
    """
    Toma UNA linea de texto del PDF y devuelve un diccionario
    con las columnas. Si la linea no es un pedido valido, devuelve None.
    """
    linea = limpiar_linea(linea)

    # Paso 1: Buscar la O.P (5 digitos al inicio)
    op_match = re.match(r'^(\d{5})\s+', linea)
    if not op_match:
        return None
    op = op_match.group(1)
    resto = linea[op_match.end():]

    # Paso 2: Buscar ITEM + DESCRIPCION (ITEM puede estar vacio)
    desc_match = re.search(r'(\d+)(TEMP\s+(?:\w+\s+)*\d+M{1,2})', resto)
    item = ""
    if desc_match:
        item = desc_match.group(1)
        desc = desc_match.group(2)
        nombre = resto[:desc_match.start()].strip()
        despues = resto[desc_match.end():].strip()
    else:
        # Caso sin ITEM (ej: ||TEMP INCOL 8MM|)
        desc_match = re.search(r'(TEMP\s+(?:\w+\s+)*\d+M{1,2})', resto)
        if not desc_match:
            return None
        desc = desc_match.group(1)
        nombre = resto[:desc_match.start()].strip()
        despues = resto[desc_match.end():].strip()

    tokens = despues.split()
    if len(tokens) < 3:
        return None

    # Paso 3: Encontrar donde esta el municipio y capturar fechas
    indice_mun, tokens, fechas = encontrar_municipio(tokens)

    # Paso 4: Reconstruir segun la posicion del municipio
    if indice_mun == 4:
        cant = tokens[0]
        ancho = tokens[1]
        alto = tokens[2]
        peso = tokens[3]

    elif indice_mun == 3:
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
                # Falta un numero: asumimos CANT=1, o usamos los 3 tal cual
                cant = "1"
                ancho = tokens[0]
                alto = tokens[1]
                peso = tokens[2]

    elif indice_mun == 2:
        # Faltan dos numeros
        cant = "1"
        ancho = tokens[0]
        alto = tokens[1]
        peso = ""

    else:
        cant = tokens[0] if len(tokens) > 0 else ""
        ancho = tokens[1] if len(tokens) > 1 else ""
        alto = tokens[2] if len(tokens) > 2 else ""
        peso = tokens[3] if len(tokens) > 3 else ""

    # Asignar fechas (maximo 2)
    fecha_op = fechas[0] if len(fechas) > 0 else ""
    fecha_sol = fechas[1] if len(fechas) > 1 else ""

    return {
        'O.P': op,
        'RAZON SOCIAL': _limpiar_nombre_cliente(nombre),
        'ITEM': item,
        'DESCRIPCION': _limpiar_descripcion(desc),
        'CANT': cant,
        'ANCHO': ancho,
        'ALTO': alto,
        'PESO': peso,
        'FECHA_O_P': fecha_op,
        'FECHA_SOL_DESPACHO': fecha_sol,
    }


def parsear_paginas(lista_paginas, log=None):
    """
    Toma una lista de paginas (texto) y devuelve una lista de diccionarios.
    Si se pasa 'log' (lista), acumula errores y advertencias.
    """
    filas = []
    ultimo_item_por_op = {}  # Para completar ITEMs vacios

    for pagina in lista_paginas:
        for linea in pagina.strip().split('\n'):
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue

            fila = parsear_linea(linea_limpia)

            if fila:
                op = fila['O.P']

                # Completar ITEM vacio con secuencia
                if fila['ITEM'] == "":
                    ultimo_item_por_op[op] = ultimo_item_por_op.get(op, 0) + 1
                    fila['ITEM'] = str(ultimo_item_por_op[op])
                else:
                    try:
                        ultimo_item_por_op[op] = int(fila['ITEM'])
                    except ValueError:
                        pass

                # Detectar campos vacios sospechosos
                campos_numericos = ['CANT', 'ANCHO', 'ALTO', 'PESO']
                vacios = [c for c in campos_numericos if fila.get(c) == ""]
                if vacios and log is not None:
                    log.append({
                        'tipo': 'sospechoso',
                        'detalle': f"Campos vacios: {', '.join(vacios)}",
                        'linea': linea_limpia,
                        'op': op,
                        'item': fila['ITEM']
                    })

                filas.append(fila)
            else:
                if log is not None:
                    log.append({
                        'tipo': 'ignorada',
                        'detalle': 'No coincidio con el patron de pedido',
                        'linea': linea_limpia,
                        'op': '',
                        'item': ''
                    })

    return filas