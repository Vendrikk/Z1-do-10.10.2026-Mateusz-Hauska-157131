"""Spotkanie 1 (26.09.2026). Te same prompty na dwóch modelach: czas, tokeny, odpowiedzi obok siebie.

Bez argumentów porównuje MODEL_A i MODEL_B z .env, czyli oba modele pobrane przez setup.
Inne modele:   python spotkanie1/s1_pokaz_02_porownaj_modele.py --modele ollama:llama3.2:3b,ollama:qwen3:8b
Jeden model:   python spotkanie1/s1_pokaz_02_porownaj_modele.py --model ollama:qwen3:8b
"""
import sys
from pathlib import Path

_katalog = Path(__file__).resolve().parent
while not (_katalog / "common.py").exists():  # szuka katalogu repozytorium w górę drzewa
    _katalog = _katalog.parent
sys.path.insert(0, str(_katalog))
import statistics
import time

from common import get_llm, modele_do_porownania, naglowek, porownaj_modele

naglowek("Porównanie modeli na pięciu promptach")

PROMPTY = [
    "Streść w jednym zdaniu: Klient zgłasza, że krem dotarł z uszkodzoną pompką i prosi o wymianę.",
    "Ile to jest 17% z 249,90 zł? Podaj sam wynik.",
    "Wypisz w formacie JSON pola: imię, miasto z tekstu: 'Piszę z Gdańska, Marta'.",
    "Czy termin 14 dni na zwrot dotyczy dni roboczych czy kalendarzowych w polskim prawie konsumenckim?",
    "Napisz uprzejmą odmowę reklamacji zgłoszonej po terminie, maksymalnie 3 zdania.",
]


def przebieg(nazwa: str) -> dict:
    """Uruchamia pięć promptów na jednym modelu i zwraca liczby do tabeli porównawczej."""
    llm = get_llm(temperature=0)          # bez argumentu: bierze model ustawiony przez porownaj_modele
    czasy, we, wy = [], 0, 0
    for p in PROMPTY:
        t0 = time.perf_counter()
        r = llm.invoke(p)
        dt = time.perf_counter() - t0
        czasy.append(dt)
        u = r.usage_metadata or {}
        we += u.get("input_tokens") or 0
        wy += u.get("output_tokens") or 0
        tresc = r.content if isinstance(r.content, str) else r.text
        print(f"\n[{dt:.2f} s | we {u.get('input_tokens')} / wy {u.get('output_tokens')}] {p[:55]}...")
        print(tresc)
    return {
        "mediana_s": round(statistics.median(czasy), 2),
        "max_s": round(max(czasy), 2),
        "tokeny_we": we,
        "tokeny_wy": wy,
    }


if __name__ == "__main__":
    modele = modele_do_porownania()
    if len(modele) == 1:
        print("Porównujesz jeden model. Ustaw MODEL_B w .env albo podaj --modele a,b,")
        print("inaczej tabela na końcu nie pokaże żadnej różnicy.\n")
    porownaj_modele(przebieg, modele, tytul="Pięć promptów na każdym modelu",
                    kolumny=["mediana_s", "max_s", "tokeny_we", "tokeny_wy"])
    print("\nOceny poprawności 0, 1, 2 wystawiasz sam i wpisujesz do WYNIKI_spotkanie1.md.")
    print("Skrypt mierzy czas i tokeny, jakości nie zmierzy za Ciebie.")
