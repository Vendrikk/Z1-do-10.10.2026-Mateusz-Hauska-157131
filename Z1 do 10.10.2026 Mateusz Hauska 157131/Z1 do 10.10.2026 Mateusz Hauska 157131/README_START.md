# Spotkanie 1: Frameworki AI, modele, tokeny i koszt (26.09.2026)

Paczka samodzielna. Zawiera wszystko, czego potrzebujesz na to spotkanie: kod, dane, konfigurację i skrypt instalacyjny. Nie wymaga niczego z poprzednich paczek.

## Instalacja jednym poleceniem

macOS albo Linux:

```
chmod +x setup.sh && ./setup.sh
```

Windows, PowerShell:

```
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Skrypt sprawdza Pythona 3.12, zakłada środowisko `.venv`, instaluje biblioteki z `requirements.txt`, tworzy `.env`, instaluje Ollamę i pobiera modele `llama3.2:3b` oraz `bge-m3`, a na końcu uruchamia test środowiska.

Jeśli nie chcesz modeli lokalnych, dodaj `--bez-ollamy` na macOS i Linuksie albo `-BezOllamy` na Windowsie. Zostanie `MODEL=fake`, które uruchamia wszystkie skrypty bez sieci i bez klucza, ale zwraca zaślepki zamiast odpowiedzi.

Model przez API ustawiasz w pliku `.env`: wpisujesz `MODEL=anthropic:claude-haiku-4-5-20251001` albo innego dostawcę i uzupełniasz klucz.

## Uruchamianie

Skrypty uruchamiasz z katalogu paczki, nie z podkatalogu:

```
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python spotkanie1/<nazwa_pliku>.py
```

## Co jest w paczce

Katalog `spotkanie1/` zawiera pliki tego spotkania: `sN_pokaz_` to kod pokazywany na zajęciach, `sN_cw_` ćwiczenie w sali z miejscami TODO, `sN_zN_` i `zN_` zadanie punktowane, `sN_cN_` ćwiczenie dodatkowe bez punktów.

Plik `WYNIKI_spotkanie1.md` to miejsce, w którym zapisujesz przewidywania przed uruchomieniem kodu i wyniki po nim.

Katalog `dane/` ma dokumenty sklepu SklepX, `eval/` zbiór testowy, `docs/adr/` szablon decyzji architektonicznej.

## Zadanie Z1

Temat: temperatura, tokeny i koszt. Oddanie do 10.10.2026, tagiem `z1` w Twoim repozytorium. Pełny opis i tabela punktów są w pliku Word „Spotkanie 1: ćwiczenia i zadanie”.

## Gdy coś nie działa

`ModuleNotFoundError: common` oznacza, że uruchamiasz skrypt spoza katalogu paczki albo bez aktywnego środowiska.

VS Code nie widzi bibliotek mimo instalacji: wybierz interpreter z `.venv` przez paletę poleceń i „Python: Select Interpreter”. Plik `.vscode/settings.json` w paczce ustawia to domyślnie.

Ollama odpowiada bardzo wolno: model nie mieści się w pamięci. Sprawdź `ollama ps` i zamknij inne modele przez `ollama stop`.
