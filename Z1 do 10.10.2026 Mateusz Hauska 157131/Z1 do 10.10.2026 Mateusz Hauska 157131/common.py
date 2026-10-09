"""Wspólna konfiguracja dla wszystkich skryptów: wybór modelu czatu i modelu embeddingów z pliku .env.

MODEL       format dostawca:model, np. anthropic:claude-haiku-4-5-20251001, ollama:llama3.2:3b,
            google_genai:gemini-2.5-flash, azure_openai:nazwa-wdrozenia albo fake (test bez sieci)
MODEL_A     model podstawowy do porównań, domyślnie to samo co MODEL
MODEL_B     model do porównania z MODEL_A, np. ollama:qwen3:8b
EMBEDDINGS  np. ollama:bge-m3, google_genai:gemini-embedding-001, openai:text-embedding-3-small,
            azure_openai:nazwa-wdrozenia albo fake

Każdy skrypt przyjmuje te same przełączniki wiersza poleceń, niezależnie od własnych argumentów:
  --model ollama:qwen3:8b       jednorazowo nadpisuje MODEL na czas tego uruchomienia
  --embeddings ollama:bge-m3    jednorazowo nadpisuje EMBEDDINGS
  --modele a,b                  lista modeli dla skryptów porównawczych
  --modele-ab                   skrót na MODEL_A i MODEL_B z .env
Przełączniki są zdejmowane z sys.argv, więc pozostałe argumenty skryptu działają jak wcześniej.
"""
import hashlib
import math
import os
import re
import typing

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

# Wszystkie ścieżki (dane/, eval/, chroma_db/, .env) liczone od katalogu repozytorium,
# niezależnie od tego, z którego katalogu uruchamiasz skrypt.
KATALOG_REPO = Path(__file__).resolve().parent
os.chdir(KATALOG_REPO)
load_dotenv(KATALOG_REPO / ".env")
MODEL = os.getenv("MODEL", "fake")
EMBEDDINGS = os.getenv("EMBEDDINGS", "fake")
_MODEL_A_ENV = os.getenv("MODEL_A", "")
MODEL_B = os.getenv("MODEL_B", "")


def _zdejmij_przelaczniki():
    """Wyjmuje z sys.argv wspólne przełączniki i zwraca listę modeli podaną w --modele."""
    global MODEL, EMBEDDINGS
    import sys
    reszta, modele, i = [sys.argv[0]], [], 1
    while i < len(sys.argv):
        a = sys.argv[i]
        nast = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
        if a in ("--model", "-m") and nast:
            MODEL = nast; i += 2
        elif a.startswith("--model="):
            MODEL = a.split("=", 1)[1]; i += 1
        elif a == "--embeddings" and nast:
            EMBEDDINGS = nast; i += 2
        elif a.startswith("--embeddings="):
            EMBEDDINGS = a.split("=", 1)[1]; i += 1
        elif a == "--modele" and nast:
            modele = [x.strip() for x in nast.split(",") if x.strip()]; i += 2
        elif a.startswith("--modele="):
            modele = [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]; i += 1
        elif a == "--modele-ab":
            modele = ["__AB__"]; i += 1
        else:
            reszta.append(a); i += 1
    sys.argv[:] = reszta
    return modele


_MODELE_Z_ARGV = _zdejmij_przelaczniki()
# MODEL_A ustalane po przetworzeniu argumentów, żeby --model wygrywał z domyślną wartością
MODEL_A = _MODEL_A_ENV or MODEL


# ---------- tryb fake: działa bez klucza i bez internetu, służy tylko do testu instalacji ----------

class FakeChat(BaseChatModel):
    """Udaje model czatu. Zwraca stałą odpowiedź i liczy tokeny jako słowa."""

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        tekst_we = " ".join(str(m.content) for m in messages)
        odpowiedz = "[fake] Nie mam tej informacji w dokumentach. Ustaw MODEL w .env, aby użyć prawdziwego modelu."
        n_in, n_out = len(tekst_we.split()), len(odpowiedz.split())
        msg = AIMessage(content=odpowiedz, usage_metadata={
            "input_tokens": n_in, "output_tokens": n_out, "total_tokens": n_in + n_out})
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def bind_tools(self, tools, **kwargs):
        return self  # fake nigdy nie wywołuje narzędzi

    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda _: _przykladowy_obiekt(schema))


def _przykladowy_obiekt(schema):
    """Buduje poprawny obiekt Pydantic z wartościami domyślnymi, żeby skrypty z wynikiem
    ustrukturyzowanym dało się uruchomić w trybie fake."""
    wartosci = {}
    for nazwa, pole in schema.model_fields.items():
        typ = pole.annotation
        if typing.get_origin(typ) is typing.Union and type(None) in typing.get_args(typ):
            wartosci[nazwa] = None
            continue
        if typing.get_origin(typ) is typing.Literal:
            wartosci[nazwa] = typing.get_args(typ)[0]
        elif typ is int or typ is float:
            minimum = next((getattr(m, "ge", None) for m in pole.metadata if hasattr(m, "ge")), 0)
            wartosci[nazwa] = typ(minimum)
        elif typ is bool:
            wartosci[nazwa] = False
        else:
            wartosci[nazwa] = "[fake]"
    return schema(**wartosci)


class HashEmbeddings(Embeddings):
    """Worek słów w 256 wymiarach. Pozwala sprawdzić potok RAG bez modelu embeddingów."""

    def _wektor(self, tekst: str) -> list[float]:
        v = [0.0] * 256
        for slowo in re.findall(r"\w+", tekst.lower()):
            v[int(hashlib.md5(slowo.encode()).hexdigest(), 16) % 256] += 1
        n = math.sqrt(sum(x * x for x in v)) or 1
        return [x / n for x in v]

    def embed_documents(self, texts):
        return [self._wektor(t) for t in texts]

    def embed_query(self, text):
        return self._wektor(text)


# ---------- funkcje używane przez skrypty ----------

def get_llm(model: str | None = None, temperature: float = 0):
    """Zwraca model czatu. Bez argumentu bierze nazwę z MODEL w .env."""
    nazwa = model or MODEL
    if nazwa == "fake":
        return FakeChat()
    from langchain.chat_models import init_chat_model
    return init_chat_model(nazwa, temperature=temperature)


def ustaw_model(nazwa: str) -> str:
    """Zmienia model używany przez get_llm() bez argumentu. Zwraca nazwę, żeby dało się ją wypisać."""
    global MODEL
    MODEL = nazwa
    return nazwa


def aktywny_model() -> str:
    """Nazwa modelu, którego użyje get_llm() bez argumentu."""
    return MODEL


def naglowek(tytul: str) -> None:
    """Wypisuje tytuł skryptu i aktywną konfigurację. Wołaj na początku każdego skryptu,
    żeby w logu z ćwiczenia było widać, na jakim modelu powstał wynik."""
    print(f"\n=== {tytul} ===")
    print(f"    model: {MODEL}    embeddingi: {EMBEDDINGS}")
    if MODEL == "fake":
        print("    uwaga: tryb fake zwraca zaślepki, wyniki nie nadają się do wniosków")
    print()


def modele_do_porownania(domyslne: list[str] | None = None) -> list[str]:
    """Lista modeli dla skryptów porównawczych, w kolejności ważności źródeł:
    --modele z wiersza poleceń, potem MODEL_A i MODEL_B z .env, potem argument domyslne,
    a na końcu sam MODEL. Zawsze zwraca co najmniej jedną nazwę, bez powtórzeń."""
    kandydaci = _MODELE_Z_ARGV
    if kandydaci == ["__AB__"] or not kandydaci:
        kandydaci = [m for m in (MODEL_A, MODEL_B) if m] or domyslne or [MODEL]
    wynik = []
    for m in kandydaci:
        if m and m not in wynik:
            wynik.append(m)
    return wynik


def porownaj_modele(zadanie, modele: list[str] | None = None, tytul: str = "Porównanie modeli",
                    kolumny: list[str] | None = None) -> list[dict]:
    """Uruchamia to samo zadanie na kolejnych modelach i wypisuje podsumowanie.

    zadanie  funkcja jednego argumentu (nazwa modelu) zwracająca słownik liczb do tabeli.
             Przed jej wywołaniem aktywny model jest przestawiany, więc get_llm() bez argumentu
             zwraca właściwy model.
    modele   lista nazw; bez niej brana jest modele_do_porownania().
    kolumny  które klucze wyniku pokazać i w jakiej kolejności; bez nich wszystkie.

    Zwraca listę słowników z dopisanym kluczem model i czas_s, żeby dało się je zapisać dalej.
    """
    import time
    lista = modele or modele_do_porownania()
    poprzedni = MODEL
    wyniki = []
    for nazwa in lista:
        ustaw_model(nazwa)
        print(f"\n----- {nazwa} -----")
        t0 = time.perf_counter()
        try:
            wynik = zadanie(nazwa) or {}
            wynik["blad"] = ""
        except Exception as e:                      # jeden model nie może przerwać porównania
            wynik = {"blad": f"{type(e).__name__}: {e}"}
            print(f"    przerwane: {wynik['blad']}")
        wynik["model"] = nazwa
        wynik["czas_s"] = round(time.perf_counter() - t0, 2)
        wyniki.append(wynik)
    ustaw_model(poprzedni)
    _tabela_podsumowania(wyniki, tytul, kolumny)
    return wyniki


def _tabela_podsumowania(wyniki: list[dict], tytul: str, kolumny: list[str] | None) -> None:
    """Wypisuje tabelę porównania i krótki komentarz o różnicach."""
    if not wyniki:
        return
    if kolumny is None:
        kolumny = []
        for w in wyniki:
            for k in w:
                if k not in ("model", "blad") and k not in kolumny:
                    kolumny.append(k)
    naglowki = ["model"] + kolumny
    wiersze = [[str(w.get("model", ""))] + [_fmt(w.get(k)) for k in kolumny] for w in wyniki]
    szer = [max(len(naglowki[i]), *(len(r[i]) for r in wiersze)) for i in range(len(naglowki))]

    print(f"\n=== {tytul} ===")
    print("  ".join(h.ljust(szer[i]) for i, h in enumerate(naglowki)))
    print("  ".join("-" * s for s in szer))
    for r in wiersze:
        print("  ".join(c.ljust(szer[i]) for i, c in enumerate(r)))

    for w in wyniki:
        if w.get("blad"):
            print(f"\nModel {w['model']} nie dokończył zadania: {w['blad']}")

    sprawne = [w for w in wyniki if not w.get("blad")]
    if len(sprawne) >= 2:
        print("\nRóżnice między modelami:")
        for k in kolumny:
            liczby = [(w["model"], w[k]) for w in sprawne if isinstance(w.get(k), (int, float))]
            if len(liczby) < 2:
                continue
            naj = max(liczby, key=lambda x: x[1])
            min_ = min(liczby, key=lambda x: x[1])
            if naj[1] == min_[1]:
                print(f"  {k}: bez różnicy ({_fmt(naj[1])})")
            else:
                print(f"  {k}: najwyżej {naj[0]} ({_fmt(naj[1])}), najniżej {min_[0]} ({_fmt(min_[1])})")
        print("\nWyższa wartość nie zawsze znaczy lepiej: przy czasie i koszcie lepiej jest niżej.")
        print("Zanim wyciągniesz wniosek, sprawdź, czy oba przebiegi miały tę samą temperaturę i te same dane.")


def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def get_embeddings():
    """Zwraca model embeddingów według EMBEDDINGS w .env."""
    if EMBEDDINGS == "fake":
        return HashEmbeddings()
    dostawca, _, model = EMBEDDINGS.partition(":")
    if dostawca == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=model)
    if dostawca == "google_genai":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=model)
    if dostawca == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model)
    if dostawca == "azure_openai":
        from langchain_openai import AzureOpenAIEmbeddings
        return AzureOpenAIEmbeddings(azure_deployment=model)
    raise ValueError(f"Nieobsługiwane EMBEDDINGS={EMBEDDINGS}")


# ---------- wspólne miary do ewaluacji (pokazy ewaluacji na zjeździe 3 i porownaj_do_excela.py) ----------

def oczekiwane_zrodla(test: dict) -> list[str]:
    """Pole oczekiwane_zrodlo może być tekstem, listą albo null (pytanie, na które system ma odmówić)."""
    z = test.get("oczekiwane_zrodlo")
    return [] if z is None else ([z] if isinstance(z, str) else list(z))


def trafienie_wyszukiwania(test: dict, zrodla: list[str]) -> bool:
    """Czy wszystkie oczekiwane dokumenty są wśród znalezionych fragmentów."""
    return all(z in zrodla for z in oczekiwane_zrodla(test))


def poprawna_odpowiedz(test: dict, odpowiedz: str) -> bool:
    """Każdy element oczekiwane_slowa musi wystąpić w odpowiedzi. Znak | oddziela warianty: '12,99|12.99'."""
    o = (odpowiedz or "").lower()
    return bool(o) and all(any(w.strip().lower() in o for w in s.split("|")) for s in test["oczekiwane_slowa"])


def zrodlo_podane(test: dict, odpowiedz: str) -> bool:
    """Czy odpowiedź cytuje właściwe dokumenty. Przy odmowie poprawnie jest nie cytować żadnego dokumentu."""
    o = (odpowiedz or "").lower()
    oczekiwane = oczekiwane_zrodla(test)
    if not oczekiwane:
        return ".md" not in o
    return all(z.lower().removesuffix(".md") in o for z in oczekiwane)


def zaladuj(sciezka: str):
    """Wczytuje skrypt z podkatalogu jako moduł, np. zaladuj("spotkanie3/s3_pokaz_03_rag_zapytanie.py").
    Nazwy plików zaczynają się od litery i cyfry, więc zwykły import by nie zadziałał."""
    import importlib.util
    plik = KATALOG_REPO / sciezka
    spec = importlib.util.spec_from_file_location(plik.stem, plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def wczytaj_json(sciezka: str, czego_brakuje: str) -> list | dict:
    """Wczytuje plik JSON z katalogu repozytorium. Gdy pliku nie ma, kończy pracę z opisem,
    co student ma utworzyć, zamiast rzucać FileNotFoundError."""
    import json
    plik = KATALOG_REPO / sciezka
    if not plik.exists():
        raise SystemExit(f"Brakuje pliku {sciezka}. {czego_brakuje}")
    try:
        return json.loads(plik.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Plik {sciezka} nie jest poprawnym JSON-em: {e}")
