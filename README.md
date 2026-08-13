<div align="center">

# 📄 PDF Pedidos → Excel

**Convierte automáticamente tus informes de pedidos en PDF a Excel.**
<br>
*Sin listas de municipios. Sin configuraciones complejas. Solo funciona.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![License](https://img.shields.io/badge/Licencia-Uso%20libre-green.svg)](./LICENSE)

</div>

---

## ✨ ¿Qué hace esta herramienta?

Tomas tus PDFs de **"Informe Resumen de Pedidos Solicitados"**, los pones en una carpeta, ejecutas un comando, y obtienes archivos Excel limpios con 8 columnas:

| O.P | RAZON SOCIAL | ITEM | DESCRIPCION | CANT | ANCHO | ALTO | PESO |
|:---:|:------------|:----:|:-----------|:----:|:-----:|:----:|:----:|

**Omite automáticamente:** Municipio, Fecha O.P, Fecha Solicitud Despacho y Observación.

### 🚀 La ventaja clave

> **No necesita lista de municipios.**
>
> El parser detecta automáticamente dónde está el municipio, así que funciona con clientes nuevos de **Cali, Pereira, Manizales, Bucaramanga, Cartagena** o cualquier ciudad que aparezca mañana. Sin actualizar listas. Sin tocar código.

---

## 📦 Instalación (5 minutos)

### 1. Clona el repositorio

```bash
git clone https://github.com/TU_USUARIO/pdf-pedidos-a-excel.git
cd pdf-pedidos-a-excel
```

### 2. Crea y activa el entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> 💡 *Verás `(venv)` al inicio de la terminal. Eso significa que estás dentro de la caja de arena.*

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

---

## 🛠️ Uso

### Opción A: Un Excel por cada PDF

1. Pon tus archivos PDF dentro de la carpeta `pdfs/`.
2. Ejecuta:

```bash
python main.py
```

3. Recoge tus archivos Excel en la carpeta `excels/`.

```
excels/
├── COM 01 - LOG (30).xlsx
├── COM 01 - LOG (31).xlsx
└── ...
```

### Opción B: Un solo Excel consolidado

```bash
python main.py --consolidar
```

Genera un único archivo `excels/CONSOLIDADO.xlsx` con todas las filas de todos los PDFs.

### Opción C: Con prefijo personalizado

```bash
python main.py --consolidar --prefijo "Agosto_"
```

Resultado: `excels/Agosto_CONSOLIDADO.xlsx`

---

## 🧠 ¿Cómo funciona el parser?

En lugar de memorizar nombres de ciudades, el parser aplica una regla simple:

> *"Después de la descripción del vidrio, lo primero que viene es un número (cantidad), luego vienen números (ancho, alto, peso), y la **primera palabra con letras** que aparezca es el municipio."*

Según **en qué posición** aparezca esa palabra, el parser sabe si los números anteriores están correctos o si se pegaron entre sí:

| Posición del municipio | Significado | Corrección automática |
|:----------------------:|:-----------|:---------------------|
| **4** | Todo normal | Ninguna |
| **3** | Falta un número | Separa `0,61,895` → `0,6` + `1,895` o `12,14` → `1` + `2,14` |
| **2** | Faltan dos números | Intenta reconstruir lo mejor posible |

Esto permite que aparezca cualquier municipio nuevo sin que tengas que actualizar código.

---

## 🧪 Tests automáticos

Para verificar que todo funciona correctamente después de cualquier cambio:

```bash
python -m pytest tests/
```

**Casos que se prueban automáticamente:**
- ✅ Línea normal con todos los datos bien puestos
- ✅ Ítem pegado al nombre del cliente (`GIL1TEMP`)
- ✅ Doble coma en ancho (`0,61,895`)
- ✅ Entero pegado a decimal (`12,14`)
- ✅ Peso pegado a municipio (`63Medellin`)
- ✅ Municipios nuevos que el parser nunca ha visto (`Cali`)

---

## 📊 Conectar con Power BI

El Excel generado es 100% compatible con Power BI:

1. Abre **Power BI Desktop**.
2. Ve a `Inicio → Obtener datos → Excel`.
3. Selecciona tu archivo `.xlsx` generado.
4. Carga la hoja **"Pedidos"**.
5. Arrastra columnas y crea visualizaciones:
   - **Barras:** Peso total por cliente.
   - **Torta:** Distribución por espesor de vidrio (5mm, 6mm, 8mm, 10mm).
   - **Mapa:** Pedidos por municipio.
   - **Tabla:** Listado detallado por orden de compra.

> 💡 *Cuando generes un Excel nuevo con la herramienta, solo presiona **Actualizar** en Power BI y los gráficos se actualizan solos.*

---

## 📁 Estructura del proyecto

```
pdf-pedidos-a-excel/
├── src/
│   ├── __init__.py          # Hace que src sea un paquete Python
│   ├── constantes.py        # Nombres de columnas (sin lista de municipios)
│   ├── extractor.py         # Lee PDFs con PyPDF2
│   ├── parser.py            # 🧠 Cerebro: interpreta el texto automáticamente
│   └── exportador.py        # Escribe archivos Excel con pandas
├── tests/
│   ├── __init__.py
│   └── test_parser.py       # Pruebas automáticas
├── pdfs/                    # 📥 Pon aquí tus PDFs de entrada
├── excels/                  # 📤 Aquí salen los Excels generados
├── main.py                  # 🎛️ Punto de entrada: ejecuta este archivo
├── requirements.txt         # Lista de dependencias
├── .gitignore               # Ignora venv/, pdfs/ y excels/
└── README.md                # 📖 Este archivo
```

---

## 🐛 ¿Qué problemas maneja automáticamente?

| Problema en el PDF | Ejemplo crudo | Resultado en Excel |
|:-------------------|:--------------|:-------------------|
| Ítem pegado al nombre | `GIL1TEMP INCOL 8MM` | Nombre: `GIL`, Ítem: `1` |
| Ancho + Alto con doble coma | `0,61,895` | Ancho: `0,6`, Alto: `1,895` |
| Entero pegado a decimal | `12,14` | Ancho: `1`, Alto: `2,14` |
| Peso pegado a municipio | `63Medellin` | Peso: `63` |
| Fechas como números seriales | `46239,58257` | Ignorado automáticamente |
| Encabezados incrustados | `14/08/2026INFORME...` | Limpieza automática |
| Municipios nuevos | `Cali`, `Pereira` | Detectados sin lista previa |

---

## ❓ Preguntas frecuentes

**¿Funciona con PDFs de otros proveedores?**
> Solo si tienen la misma estructura: 5 dígitos de O.P, nombre del cliente, número de ítem, descripción `TEMP [COLOR] [ESPESOR]MM`, y luego los números. Si el formato cambia, el parser necesitará ajustes.

**¿Y si el PDF es una imagen escaneada?**
> No. Esta herramienta lee texto plano. Si el PDF es una foto de un papel, necesitarías OCR (reconocimiento óptico de caracteres), que es otra tecnología distinta.

**¿Puedo agregar más columnas al Excel?**
> Sí. Edita `src/constantes.py` y agrega el nombre de la columna. Luego actualiza `src/parser.py` para extraer ese dato del texto.

**¿Es seguro subir los PDFs a GitHub?**
> No. Por eso `pdfs/` y `excels/` están en `.gitignore`. GitHub es para código, no para datos de la empresa.

---

## 📝 Licencia

Uso libre para fines internos de tu empresa.

---

<div align="center">

Hecho con 💻 y ☕ para automatizar lo aburrido.

</div>
