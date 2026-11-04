"""Restore UTF-8 Spanish text after Windows PowerShell's ASCII pipeline conversion."""
from pathlib import Path

path = Path("docs/local_model_gemma4_viability.md")
text = path.read_text(encoding="utf-8")
replacements = {
    "ci?n": "ción", "si?n": "sión", "?ndice": "índice", "?nica": "única",
    "?nico": "único", "?nicamente": "únicamente", "?ntegramente": "íntegramente",
    "?ntegro": "íntegro", "?rbol": "árbol", "?xito": "Éxito", "Bogot?": "Bogotá",
    "L?mite": "Límite", "l?mite": "límite", "Ning?n": "Ningún", "ning?n": "ningún",
    "Pol?tica": "Política", "Reconoci?": "Reconoció", "Tama?o": "Tamaño",
    "tama?o": "tamaño", "Despu?s": "Después", "despu?s": "después", "a?ade": "añade",
    "a?adi?": "añadió", "a?adieron": "añadieron", "a?adir": "añadir", "acompa?a": "acompaña",
    "actualiz?": "actualizó", "adem?s": "además", "adquiri?": "adquirió", "an?lisis": "análisis",
    "aplic?": "aplicó", "aqu?": "aquí", "autom?tica": "automática", "c?digo": "código",
    "c?lculo": "cálculo", "cambi?": "cambió", "campa?a": "campaña", "can?nico": "canónico",
    "cat?logo": "catálogo", "cient?fic": "científic", "comprob?": "comprobó", "confirm?": "confirmó",
    "contin?a": "continúa", "continu?": "continuó", "corrigi?": "corrigió", "cr?tica": "crítica",
    "cre?": "creó", "descarg?": "descargó", "desplazar?an": "desplazarían", "diagn?stic": "diagnóstic",
    "din?mica": "dinámica", "ejecut?": "ejecutó", "est?": "está", "expl?cita": "explícita",
    "f?sica": "física", "fall?": "falló", "hab?a": "había", "hist?ric": "históric",
    "id?nticos": "idénticos", "instal?": "instaló", "leg?tima": "legítima", "liber?": "liberó",
    "lleg?": "llegó", "m?nima": "mínima", "m?nimo": "mínimo", "m?tricas": "métricas",
    "m?xima": "máxima", "m?ximo": "máximo", "p?blicos": "públicos", "par?metros": "parámetros",
    "peque?a": "pequeña", "qued?": "quedó", "ra?z": "raíz", "rechaz?": "rechazó",
    "repiti?": "repitió", "resolvi?": "resolvió", "respet?": "respetó", "seg?n": "según",
    "segu?an": "seguían", "sem?ntic": "semántic", "sigui?": "siguió", "simult?neamente": "simultáneamente",
    "super?": "superó", "taxonom?a": "taxonomía", "termin?": "terminó", "v?lida": "válida",
    "vac?a": "vacía", "vac?o": "vacío", "volvi?": "volvió", "1?3": "1–3",
    "12B ? resultado": "12B — resultado", "| ? |": "| ∅ |", "| ? /": "| ∅ /",
    "congelada: ?.": "congelada: ∅.",
}
for before, after in replacements.items():
    text = text.replace(before, after)
assert "?" not in text, sorted(set(word for word in text.split() if "?" in word))
path.write_text(text, encoding="utf-8", newline="\n")
print("Report restored as UTF-8; no question-mark substitutions remain.")
