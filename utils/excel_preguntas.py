"""
Lectura de preguntas de opción múltiple desde Excel (.xlsx) o CSV.

Formato esperado (los encabezados aceptan variantes, mayúsculas y acentos):
    pregunta | opcion1 | opcion2 | opcion3 | opcion4 | respuesta_correcta

La respuesta correcta puede escribirse como el texto de la opción,
como letra (A, B, C, D) o como número (1, 2, 3, 4).
"""
import math
import re
import unicodedata

import pandas as pd

MAX_OPCIONES = 6
LETRAS = "ABCDEF"


class ErrorExcel(ValueError):
    """Error con un mensaje listo para mostrar al profesor."""


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def _celda(valor):
    """Convierte una celda a texto limpio ('' si está vacía)."""
    if valor is None:
        return ""
    if isinstance(valor, float):
        if math.isnan(valor):
            return ""
        if valor.is_integer():
            return str(int(valor))
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    return str(valor).strip()


def _columnas(df):
    """Identifica qué columna es la pregunta, las opciones y la respuesta."""
    pregunta = respuesta = None
    opciones = {}
    for col in df.columns:
        n = _normalizar(col)
        if n in ("pregunta", "enunciado", "preguntas", "reactivo"):
            pregunta = col
        elif n in ("respuestacorrecta", "respuesta", "correcta", "respuestas"):
            respuesta = col
        else:
            m = re.fullmatch(r"(?:opcion|opciones|inciso|op)([1-6a-f])", n)
            if m:
                clave = m.group(1)
                indice = int(clave) if clave.isdigit() else LETRAS.lower().index(clave) + 1
                opciones[indice] = col
    return pregunta, [opciones[k] for k in sorted(opciones)], respuesta


def leer_preguntas(archivo):
    """
    Devuelve una lista de dicts {enunciado, opciones, respuesta_correcta, tipo}.
    Lanza ErrorExcel con un mensaje claro si el archivo no es válido.
    """
    if archivo is None or not getattr(archivo, "filename", ""):
        raise ErrorExcel("No se recibió ningún archivo.")

    nombre = archivo.filename.lower()
    try:
        if nombre.endswith(".csv"):
            df = pd.read_csv(archivo, dtype=object)
        elif nombre.endswith((".xlsx", ".xlsm")):
            df = pd.read_excel(archivo, dtype=object, engine="openpyxl")
        else:
            raise ErrorExcel("Formato no soportado. Usa un archivo .xlsx o .csv.")
    except ErrorExcel:
        raise
    except Exception:
        raise ErrorExcel("No se pudo leer el archivo. Verifica que sea un Excel (.xlsx) válido.")

    col_pregunta, col_opciones, col_respuesta = _columnas(df)
    faltan = []
    if col_pregunta is None:
        faltan.append("pregunta")
    if len(col_opciones) < 2:
        faltan.append("opcion1, opcion2…")
    if col_respuesta is None:
        faltan.append("respuesta_correcta")
    if faltan:
        raise ErrorExcel(
            "Faltan columnas en el Excel: " + ", ".join(faltan)
            + ". Usa los encabezados: pregunta, opcion1, opcion2, opcion3, opcion4, respuesta_correcta."
        )

    preguntas, errores = [], []
    for i, fila in df.iterrows():
        num_fila = i + 2  # fila 1 = encabezados
        enunciado = _celda(fila[col_pregunta])
        opciones = [_celda(fila[c]) for c in col_opciones[:MAX_OPCIONES]]
        respuesta = _celda(fila[col_respuesta])

        if not enunciado and not any(opciones) and not respuesta:
            continue  # fila vacía

        opciones = [o for o in opciones if o]
        if not enunciado:
            errores.append(f"Fila {num_fila}: falta el texto de la pregunta.")
            continue
        if len(opciones) < 2:
            errores.append(f"Fila {num_fila}: necesita al menos 2 opciones.")
            continue

        # Respuesta como texto, letra (A-D) o número (1-4)
        correcta = next((o for o in opciones if o.lower() == respuesta.lower()), None)
        if correcta is None and len(respuesta) == 1 and respuesta.upper() in LETRAS[:len(opciones)]:
            correcta = opciones[LETRAS.index(respuesta.upper())]
        if correcta is None and respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            correcta = opciones[int(respuesta) - 1]
        if correcta is None:
            errores.append(
                f"Fila {num_fila}: la respuesta correcta «{respuesta or 'vacía'}» no coincide con ninguna opción."
            )
            continue

        preguntas.append({
            "tipo": "multiple",
            "enunciado": enunciado,
            "opciones": opciones,
            "respuesta_correcta": correcta,
        })

    if errores:
        raise ErrorExcel("Revisa tu Excel:\n" + "\n".join(errores[:10])
                         + ("\n…" if len(errores) > 10 else ""))
    if not preguntas:
        raise ErrorExcel("El Excel no tiene preguntas.")
    return preguntas
