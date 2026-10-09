"""Spotkanie 1 (26.09.2026). Pierwsze wywołanie modelu: wiadomości, strumieniowanie, zużycie tokenów."""
import sys
from pathlib import Path

_katalog = Path(__file__).resolve().parent
while not (_katalog / "common.py").exists():  # szuka katalogu repozytorium w górę drzewa
    _katalog = _katalog.parent
sys.path.insert(0, str(_katalog))
import time
from langchain_core.messages import SystemMessage, HumanMessage
from common import get_llm, naglowek

naglowek("Pierwsze wywołanie modelu: wiadomości, strumieniowanie, zużycie tokenów")

llm = get_llm()

messages = [
    SystemMessage(content="Jesteś asystentem działu obsługi klienta. Odpowiadasz krótko, po polsku."),
    HumanMessage(content="Klient pyta, ile trwa rozpatrzenie reklamacji. Co odpowiedzieć?"),
]

start = time.perf_counter()
response = llm.invoke(messages)
elapsed = time.perf_counter() - start

print(response.content)
print("Czas odpowiedzi [s]:", round(elapsed, 2))
print("Zużycie tokenów:", response.usage_metadata)  # input_tokens, output_tokens, total_tokens

print("\n--- strumieniowanie ---")
for chunk in llm.stream("Wymień trzy powody zwrotu towaru w sklepie internetowym."):
    print(chunk.content, end="", flush=True)
print()
