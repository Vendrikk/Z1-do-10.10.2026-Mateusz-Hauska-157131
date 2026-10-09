
"""Spotkanie 1 (26.09.2026).
ZADANIE Z1: temperatura, tokeny i koszt.

Uruchom:
python spotkanie1/s1_z1_temperatura_tokeny.py
"""
import sys
from pathlib import Path

_katalog = Path(__file__).resolve().parent

while not (_katalog / "common.py").exists():
    if _katalog == _katalog.parent:
        raise FileNotFoundError("Nie znaleziono pliku common.py")
    _katalog = _katalog.parent

sys.path.insert(0, str(_katalog))

from common import MODEL, get_llm, naglowek

naglowek("ZADANIE Z1: temperatura, tokeny i koszt")

PROMPT = "Zaproponuj nazwę dla nowego serum z witaminą C. Podaj tylko nazwę."

ZDANIE_PL = (
    "Klient zgłasza, że krem dotarł z uszkodzoną pompką "
    "i prosi o wymianę."
)

ZDANIE_EN = (
    "The customer reports that the cream arrived with "
    "a damaged pump and asks for a replacement."
)

def rozne_odpowiedzi(temperatura: float, powtorzenia: int = 5) -> set[str]:
    """Wywołuje model kilka razy i zbiera różne odpowiedzi."""

    llm = get_llm(temperature=temperatura)
    odpowiedzi = set()

    for _ in range(powtorzenia):
        wynik = llm.invoke(PROMPT)
        odpowiedzi.add(str(wynik.content).strip())

    return odpowiedzi

def tokeny_wejsciowe(tekst: str) -> int:
    """Zwraca liczbę tokenów wejściowych."""

    llm = get_llm(temperature=0)
    odpowiedz = llm.invoke(tekst)

    metadane = odpowiedz.usage_metadata or {}

    if "input_tokens" not in metadane:
        raise RuntimeError("Brak informacji o tokenach wejściowych.")

    return int(metadane["input_tokens"])

def koszt_miesieczny(
    tokeny_we: int,
    tokeny_wy: int,
    zapytan: int,
    cena_we: float,
    cena_wy: float
) -> float:
    """Koszt USD przy stawkach za 1 mln tokenów."""

    return zapytan * (
        tokeny_we * cena_we + tokeny_wy * cena_wy
    ) / 1_000_000

def test_ucinania_zdania():
    """Szuka limitu, przy którym odpowiedź zostaje ucięta."""

    prompt = (
        "Napisz jeden długi akapit składający się z co najmniej "
        "10 zdań o zaletach stosowania witaminy C w kosmetykach. "
        "Nie używaj list ani wypunktowań."
    )

    llm = get_llm(temperature=0)

    for limit in range(10, 101, 5):

        model = llm.bind(options={"num_predict": limit})
        odpowiedz = model.invoke(prompt)

        tekst = str(odpowiedz.content).strip()
        metadane = odpowiedz.usage_metadata or {}
        tokeny_wy = metadane.get("output_tokens", 0)

        zakonczone_zdanie = tekst.endswith((".", "!", "?"))
        osiagnieto_limit = tokeny_wy >= limit

        uciete = osiagnieto_limit and not zakonczone_zdanie

        print(f"\n=== LIMIT: {limit} TOKENÓW ===")
        print(f"Odpowiedź: {tekst}")
        print(f"Tokeny wyjściowe: {tokeny_wy}")

        if uciete:
            print("Czy odpowiedź została ucięta w połowie zdania? TAK")
            print(f"Znaleziony limit: {limit} tokenów")
            break
        else:
            print("Czy odpowiedź została ucięta w połowie zdania? NIE")

    else:
        print("Nie znaleziono uciętej odpowiedzi.")

# 5. Koszt 1 zapytania i 10000 zapytań

def test_kosztu_zapytania():
    """Mierzy tokeny jednego zapytania i przelicza miesięczne zużycie."""

    llm = get_llm(temperature=0)
    odpowiedz = llm.invoke(PROMPT)

    metadane = odpowiedz.usage_metadata or {}

    tokeny_we = int(metadane["input_tokens"])
    tokeny_wy = int(metadane["output_tokens"])

    liczba_zapytan = 10_000

    print("\n=== KOSZT JEDNEGO ZAPYTANIA ===")
    print(f"Odpowiedź modelu: {odpowiedz.content}")
    print(f"Tokeny wejściowe: {tokeny_we}")
    print(f"Tokeny wyjściowe: {tokeny_wy}")
    print(f"Łącznie tokenów: {tokeny_we + tokeny_wy}")

    print("\n=== KOSZT 10 000 ZAPYTAŃ MIESIĘCZNIE ===")
    print(f"Tokeny wejściowe: {tokeny_we * liczba_zapytan}")
    print(f"Tokeny wyjściowe: {tokeny_wy * liczba_zapytan}")
    print(f"Łącznie tokenów: {(tokeny_we + tokeny_wy) * liczba_zapytan}")

    # Lokalna Ollama nie pobiera opłat za tokeny.
    cena_we = 0.0
    cena_wy = 0.0

    koszt_jeden = koszt_miesieczny(
        tokeny_we, tokeny_wy, 1, cena_we, cena_wy
    )

    koszt_10k = koszt_miesieczny(
        tokeny_we, tokeny_wy, liczba_zapytan, cena_we, cena_wy
    )

    print(f"Koszt jednego zapytania: {koszt_jeden:.2f} USD")
    print(f"Koszt 10 000 zapytań: {koszt_10k:.2f} USD")
    print("Źródło: https://ollama.com/pricing")
    print("Data odczytu: 09.10.2026")
    print("Uwaga: nie uwzględniono kosztów prądu i sprzętu.")

if __name__ == "__main__":

    print(f"Model: {MODEL}\n")

    # Temperatura 0 I 1

    for t in (0, 1):
        odp = rozne_odpowiedzi(t)

        print(
            f"Temperatura {t}: {len(odp)} różnych odpowiedzi "
            f"na 5 wywołań: {odp}"
        )

    # Tokeny polskie i angielskie

    pl = tokeny_wejsciowe(ZDANIE_PL)
    en = tokeny_wejsciowe(ZDANIE_EN)

    print(
        f"\nTokeny wejściowe PL: {pl}, EN: {en}, "
        f"różnica: {pl / en - 1:+.0%}"
    )

    # Przykładowe koszty

    print(
        "\nPrzykładowy koszt 10 000 zapytań, tańszy model: "
        f"{koszt_miesieczny(400, 200, 10_000, 1.0, 5.0):.2f} USD"
    )

    print(
        "Przykładowy koszt 10 000 zapytań, droższy model: "
        f"{koszt_miesieczny(400, 200, 10_000, 5.0, 25.0):.2f} USD"
    )

    # Test ucinania zdania

    print("\n AUTOMATYCZNY TEST UCINANIA ZDANIA")
    test_ucinania_zdania()
    # Pomiar kosztu zapytania
    test_kosztu_zapytania()
