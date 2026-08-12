from PyPDF2 import PdfReader
from pathlib import Path


def extraer_texto_pdf(ruta_pdf):
    """
    Abre un PDF y devuelve una lista con el texto de cada pagina.

    Args:
        ruta_pdf: ruta al archivo PDF (string o Path)

    Returns:
        lista de strings, donde cada string es el texto de una pagina
    """
    ruta = Path(ruta_pdf)
    lector = PdfReader(str(ruta))

    paginas = []
    for pagina in lector.pages:
        texto = pagina.extract_text()
        if texto:
            paginas.append(texto)

    return paginas