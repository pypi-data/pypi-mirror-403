import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


def _similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def buscar_municipio(
    frase: str,
    municipios_file: str | Path | None = None,
    umbral: float = 0.85
):
    """
    Busca un municipio español dentro de una frase.

    Args:
        frase (str): texto a analizar
        municipios_file (str|Path|None): ruta alternativa al archivo municipios.txt
        umbral (float): porcentaje mínimo de similitud (0–1)

    Returns:
        dict | None
    """

    if municipios_file is None:
        municipios_file = Path(__file__).parent / "municipios.txt"

    frase_norm = _normalizar(frase)

    mejor = None
    mejor_score = 0.0

    with open(municipios_file, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or ";" not in linea:
                continue

            provincia, municipio = linea.split(";", 1)
            municipio_norm = _normalizar(municipio)

            score = _similitud(frase_norm, municipio_norm)

            if score >= umbral and score > mejor_score:
                mejor_score = score
                mejor = {
                    "provincia": provincia,
                    "municipio": municipio,
                    "score": round(score, 3),
                }

    return mejor
