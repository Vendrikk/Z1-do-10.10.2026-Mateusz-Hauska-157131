"""Sprawdza środowisko przed pierwszymi zajęciami. Wynik wyślij prowadzącemu jako zrzut ekranu.
Uruchom: python 00_sprawdz_srodowisko.py"""
import importlib.metadata as md
import json
import platform
import sys
import urllib.request
from pathlib import Path

wyniki = []


def sprawdz(nazwa, warunek, uwaga=""):
    wyniki.append(warunek)
    print(f"[{'OK ' if warunek else 'BŁĄD'}] {nazwa}" + (f"  ({uwaga})" if uwaga else ""))


print(f"System: {platform.system()} {platform.release()} {platform.machine()}")
sprawdz(f"Python {sys.version.split()[0]}", sys.version_info >= (3, 11), "wymagany 3.11 lub nowszy, zalecany 3.12")
sprawdz("Wirtualne środowisko aktywne", sys.prefix != sys.base_prefix, "aktywuj: source .venv/bin/activate")

for pakiet in ["langchain", "langchain-core", "langgraph", "langchain-chroma", "chromadb",
               "langchain-anthropic", "langchain-ollama", "langchain-classic", "rank-bm25"]:
    try:
        sprawdz(f"{pakiet} {md.version(pakiet)}", True)
    except md.PackageNotFoundError:
        sprawdz(pakiet, False, "pip install -r requirements.txt")

sprawdz("Plik .env", Path(".env").exists(), "cp .env.example .env")
sprawdz("Katalog dane/ z dokumentami", len(list(Path("dane").glob("*.md"))) > 0)

from common import EMBEDDINGS, MODEL, get_embeddings, get_llm  # noqa: E402

print(f"MODEL={MODEL}  EMBEDDINGS={EMBEDDINGS}")
if "ollama" in MODEL or "ollama" in EMBEDDINGS:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            modele = [m["name"] for m in json.loads(r.read())["models"]]
        sprawdz("Ollama działa", True, ", ".join(modele) or "brak pobranych modeli")
    except Exception:
        sprawdz("Ollama działa", False, "uruchom aplikację Ollama albo: ollama serve")

try:
    odp = get_llm().invoke("Odpowiedz jednym słowem: działa?")
    sprawdz("Wywołanie modelu czatu", True, str(odp.content)[:60])
except Exception as e:
    sprawdz("Wywołanie modelu czatu", False, f"{type(e).__name__}: {str(e)[:80]}")

try:
    wektor = get_embeddings().embed_query("test")
    sprawdz("Embeddingi", len(wektor) > 0, f"wymiar {len(wektor)}")
except Exception as e:
    sprawdz("Embeddingi", False, f"{type(e).__name__}: {str(e)[:80]}")

print("\nWYNIK:", "wszystko działa" if all(wyniki) else f"błędów: {wyniki.count(False)}, popraw i uruchom ponownie")
