#!/usr/bin/env bash
# Przygotowanie całego środowiska od zera. macOS i Linux.
# Uruchom w katalogu tej paczki:
#   chmod +x setup.sh && ./setup.sh
# Bez modeli lokalnych (sam Python i biblioteki):
#   ./setup.sh --bez-ollamy
set -e

BEZ_OLLAMY=0
[ "$1" = "--bez-ollamy" ] && BEZ_OLLAMY=1

# Dwa modele czatu do ćwiczeń porównawczych i jeden model embeddingów.
# Podmień przez zmienne środowiskowe, np.:  MODEL_B_NAZWA=qwen3:14b ./setup.sh
MODEL_A_NAZWA="${MODEL_A_NAZWA:-llama3.2:3b}"
MODEL_B_NAZWA="${MODEL_B_NAZWA:-qwen3:8b}"
EMB_NAZWA="${EMB_NAZWA:-bge-m3}"

SYSTEM="$(uname -s)"
echo "System: $SYSTEM"
echo ""

# ---------------------------------------------------------------- 1. Python 3.12
echo "1/6  Python 3.12"
PY=""
for kandydat in python3.12 python3 python; do
  if command -v "$kandydat" >/dev/null 2>&1; then
    WERSJA="$("$kandydat" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0.0")"
    case "$WERSJA" in
      3.12|3.13) PY="$kandydat"; break ;;
    esac
  fi
done

if [ -z "$PY" ]; then
  if [ "$SYSTEM" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      echo "     Instaluję python@3.12 przez Homebrew"
      brew install python@3.12
      PY="$(brew --prefix python@3.12)/bin/python3.12"
    else
      echo "     Brak Pythona 3.12 i brak Homebrew."
      echo "     Zainstaluj Homebrew ze strony https://brew.sh albo Pythona ze strony https://www.python.org/downloads/"
      exit 1
    fi
  else
    echo "     Brak Pythona 3.12. Na Ubuntu i Debianie:"
    echo "       sudo apt update && sudo apt install -y python3.12 python3.12-venv"
    exit 1
  fi
fi
echo "     Używam: $PY ($("$PY" --version))"

# ---------------------------------------------------------------- 2. venv
echo "2/6  Wirtualne środowisko .venv"
# Sprawdzamy plik aktywacyjny, a nie sam katalog: przerwana instalacja zostawia pusty .venv,
# który wygląda jak gotowe środowisko i wywala skrypt dopiero przy source.
if [ -d .venv ] && [ ! -f .venv/bin/activate ]; then
  echo "     Znalazłem niekompletny .venv z przerwanej instalacji, usuwam"
  rm -rf .venv
fi
if [ ! -f .venv/bin/activate ]; then
  "$PY" -m venv .venv
  echo "     Utworzone"
else
  echo "     Już istnieje, używam istniejącego"
fi
if [ ! -f .venv/bin/activate ]; then
  echo ""
  echo "     Nie udało się utworzyć środowiska. Najczęstsza przyczyna to Python bez modułu venv."
  echo "     Sprawdź ręcznie:  $PY -m venv .venv"
  echo "     macOS:   brew install python@3.12"
  echo "     Ubuntu:  sudo apt install -y python3.12-venv"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip -q

# ---------------------------------------------------------------- 3. biblioteki
echo "3/6  Biblioteki z requirements.txt (pierwszy raz kilka minut)"
pip install -r requirements.txt -q
echo "     Zainstalowane"

# ---------------------------------------------------------------- 4. .env
echo "4/6  Plik konfiguracji .env"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "     Utworzony z .env.example, domyślnie MODEL=fake"
else
  echo "     Już istnieje, nie nadpisuję"
fi

# ---------------------------------------------------------------- 5. Ollama
echo "5/6  Modele lokalne (Ollama)"
if [ "$BEZ_OLLAMY" = "1" ]; then
  echo "     Pominięte na żądanie (--bez-ollamy)"
else
  if ! command -v ollama >/dev/null 2>&1; then
    if [ "$SYSTEM" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
      brew install --cask ollama || true
    elif [ "$SYSTEM" = "Linux" ]; then
      echo "     Instaluję Ollamę skryptem ze strony ollama.com"
      curl -fsSL https://ollama.com/install.sh | sh || true
    fi
  fi

  if command -v ollama >/dev/null 2>&1; then
    if ! curl -s http://localhost:11434 >/dev/null 2>&1; then
      [ "$SYSTEM" = "Darwin" ] && open -a Ollama 2>/dev/null || true
      echo "     Czekam na uruchomienie serwera Ollamy"
      for _ in $(seq 1 30); do
        curl -s http://localhost:11434 >/dev/null 2>&1 && break
        sleep 1
      done
    fi
    if curl -s http://localhost:11434 >/dev/null 2>&1; then
      echo "     Pobieram model A: $MODEL_A_NAZWA"
      ollama pull "$MODEL_A_NAZWA"
      echo "     Pobieram model B: $MODEL_B_NAZWA (do ćwiczeń porównawczych)"
      if ! ollama pull "$MODEL_B_NAZWA"; then
        echo "     Nie udało się pobrać $MODEL_B_NAZWA. Sprawdź nazwę na ollama.com/library"
        echo "     i pobierz ręcznie: ollama pull <nazwa>, potem wpisz ją do MODEL_B w .env."
        MODEL_B_NAZWA=""
      fi
      echo "     Pobieram embeddingi: $EMB_NAZWA (obsługa polskiego)"
      ollama pull "$EMB_NAZWA"
      echo "     Przełączam .env na modele lokalne"
      # fake zostaje jako zakomentowany wariant, a linia ollama przestaje być komentarzem,
      # dzięki czemu w pliku nie robi się duplikat aktywnej linii i jej kopii w komentarzu
      if [ "$SYSTEM" = "Darwin" ]; then SED=(sed -i ''); else SED=(sed -i); fi
      if grep -q '^MODEL=fake' .env; then
        "${SED[@]}" -e 's/^MODEL=fake/# MODEL=fake/' \
                    -e 's/^# MODEL=ollama:llama3.2:3b/MODEL=ollama:llama3.2:3b/' .env
      fi
      if grep -q '^EMBEDDINGS=fake' .env; then
        "${SED[@]}" -e 's/^EMBEDDINGS=fake/# EMBEDDINGS=fake/' \
                    -e 's/^# EMBEDDINGS=ollama:bge-m3/EMBEDDINGS=ollama:bge-m3/' .env
      fi
      # MODEL_A i MODEL_B: para do ćwiczeń porównawczych
      "${SED[@]}" -e "s|^MODEL_A=.*|MODEL_A=ollama:${MODEL_A_NAZWA}|" .env
      if [ -n "$MODEL_B_NAZWA" ]; then
        "${SED[@]}" -e "s|^MODEL_B=.*|MODEL_B=ollama:${MODEL_B_NAZWA}|" .env
      fi
      if [ "$EMB_NAZWA" != "bge-m3" ]; then
        "${SED[@]}" -e "s|^EMBEDDINGS=.*|EMBEDDINGS=ollama:${EMB_NAZWA}|" .env
      fi
    else
      echo "     Serwer Ollamy nie odpowiada. Zostaje MODEL=fake, możesz to zmienić później w .env"
    fi
  else
    echo "     Ollamy nie udało się zainstalować. Pobierz ją ze strony https://ollama.com"
    echo "     Zostaje MODEL=fake, wystarczy do sprawdzenia instalacji"
  fi
fi

# ---------------------------------------------------------------- 6. test
echo "6/6  Sprawdzenie środowiska"
python 00_sprawdz_srodowisko.py

echo ""
echo "Gotowe."
echo "W każdym nowym terminalu aktywuj środowisko:  source .venv/bin/activate"
echo "Skrypty uruchamiaj z tego katalogu, na przykład:  python spotkanie1/s1_pokaz_01_pierwsze_wywolanie.py"
echo ""
echo "Masz dwa modele czatu ustawione w .env jako MODEL_A i MODEL_B."
echo "Skrypty porównawcze bez argumentów uruchomią oba i zestawią wyniki w jednej tabeli:"
echo "  python spotkanie1/s1_pokaz_02_porownaj_modele.py"
echo "Jeden model na raz:   python <skrypt>.py --model ollama:${MODEL_A_NAZWA}"
echo "Własna para modeli:   python <skrypt>.py --modele ollama:a,ollama:b"
