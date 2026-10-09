# Przygotowanie całego środowiska od zera. Windows, PowerShell.
# Uruchom w katalogu tej paczki:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Bez modeli lokalnych:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1 -BezOllamy

param([switch]$BezOllamy, [string]$ModelA = "llama3.2:3b", [string]$ModelB = "qwen3:8b", [string]$Emb = "bge-m3")
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------- 1. Python
Write-Host "1/6  Python 3.12"
$py = $null
foreach ($kandydat in @("py -3.12", "py -3.13", "python")) {
    $czesci = $kandydat.Split(" ")
    try {
        $wersja = & $czesci[0] $czesci[1..($czesci.Length-1)] -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($wersja -eq "3.12" -or $wersja -eq "3.13") { $py = $kandydat; break }
    } catch { }
}
if (-not $py) {
    Write-Host "     Brak Pythona 3.12. Zainstaluj go poleceniem:"
    Write-Host "       winget install Python.Python.3.12"
    Write-Host "     albo ze strony https://www.python.org/downloads/ (zaznacz Add python.exe to PATH)."
    exit 1
}
Write-Host "     Uzywam: $py"

# ---------------------------------------------------------------- 2. venv
Write-Host "2/6  Wirtualne srodowisko .venv"
$python = ".\.venv\Scripts\python.exe"
# Sprawdzamy plik interpretera, a nie sam katalog: przerwana instalacja zostawia pusty .venv
if ((Test-Path ".venv") -and -not (Test-Path $python)) {
    Write-Host "     Znalazlem niekompletny .venv z przerwanej instalacji, usuwam"
    Remove-Item -Recurse -Force ".venv"
}
if (-not (Test-Path $python)) {
    $czesci = $py.Split(" ")
    & $czesci[0] $czesci[1..($czesci.Length-1)] -m venv .venv
    Write-Host "     Utworzone"
} else {
    Write-Host "     Juz istnieje, uzywam istniejacego"
}
if (-not (Test-Path $python)) {
    Write-Host ""
    Write-Host "     Nie udalo sie utworzyc srodowiska. Sprawdz recznie:  $py -m venv .venv"
    exit 1
}
& $python -m pip install --upgrade pip -q

# ---------------------------------------------------------------- 3. biblioteki
Write-Host "3/6  Biblioteki z requirements.txt (pierwszy raz kilka minut)"
& $python -m pip install -r requirements.txt -q
Write-Host "     Zainstalowane"

# ---------------------------------------------------------------- 4. .env
Write-Host "4/6  Plik konfiguracji .env"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "     Utworzony z .env.example, domyslnie MODEL=fake"
} else {
    Write-Host "     Juz istnieje, nie nadpisuje"
}

# ---------------------------------------------------------------- 5. Ollama
Write-Host "5/6  Modele lokalne (Ollama)"
if ($BezOllamy) {
    Write-Host "     Pominiete na zadanie (-BezOllamy)"
} else {
    $maOllame = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $maOllame) {
        $maWinget = Get-Command winget -ErrorAction SilentlyContinue
        if ($maWinget) {
            Write-Host "     Instaluje Ollame przez winget"
            winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $maOllame = Get-Command ollama -ErrorAction SilentlyContinue
        }
    }
    if ($maOllame) {
        Write-Host "     Pobieram model A: $ModelA"
        ollama pull $ModelA
        Write-Host "     Pobieram model B: $ModelB (do cwiczen porownawczych)"
        ollama pull $ModelB
        if ($LASTEXITCODE -ne 0) {
            Write-Host "     Nie udalo sie pobrac $ModelB. Sprawdz nazwe na ollama.com/library"
            Write-Host "     i pobierz recznie, potem wpisz ja do MODEL_B w .env."
            $ModelB = ""
        }
        Write-Host "     Pobieram embeddingi: $Emb"
        ollama pull $Emb
        Write-Host "     Przelaczam .env na modele lokalne"
        # fake zostaje jako zakomentowany wariant, linia ollama przestaje byc komentarzem
        $tresc = Get-Content ".env"
        if ($tresc -match "^MODEL=fake") {
            $tresc = $tresc -replace "^MODEL=fake", "# MODEL=fake" `
                            -replace "^# MODEL=ollama:llama3\.2:3b", "MODEL=ollama:llama3.2:3b"
        }
        if ($tresc -match "^EMBEDDINGS=fake") {
            $tresc = $tresc -replace "^EMBEDDINGS=fake", "# EMBEDDINGS=fake" `
                            -replace "^# EMBEDDINGS=ollama:bge-m3", "EMBEDDINGS=ollama:bge-m3"
        }
        $tresc = $tresc -replace "^MODEL_A=.*", "MODEL_A=ollama:$ModelA"
        if ($ModelB) { $tresc = $tresc -replace "^MODEL_B=.*", "MODEL_B=ollama:$ModelB" }
        if ($Emb -ne "bge-m3") { $tresc = $tresc -replace "^EMBEDDINGS=.*", "EMBEDDINGS=ollama:$Emb" }
        $tresc | Set-Content ".env"
    } else {
        Write-Host "     Ollamy nie udalo sie zainstalowac. Pobierz ja ze strony https://ollama.com"
        Write-Host "     Zostaje MODEL=fake, wystarczy do sprawdzenia instalacji"
    }
}

# ---------------------------------------------------------------- 6. test
Write-Host "6/6  Sprawdzenie srodowiska"
& $python 00_sprawdz_srodowisko.py

Write-Host ""
Write-Host "Gotowe."
Write-Host "W kazdym nowym terminalu aktywuj srodowisko:  .\.venv\Scripts\activate"
Write-Host "Skrypty uruchamiaj z tego katalogu, na przyklad:  python spotkanie1\s1_pokaz_01_pierwsze_wywolanie.py"
Write-Host ""
Write-Host "Masz dwa modele czatu ustawione w .env jako MODEL_A i MODEL_B."
Write-Host "Skrypty porownawcze bez argumentow uruchomia oba i zestawia wyniki w jednej tabeli:"
Write-Host "  python spotkanie1\s1_pokaz_02_porownaj_modele.py"
Write-Host "Jeden model na raz:   python <skrypt>.py --model ollama:$ModelA"
Write-Host "Wlasna para modeli:   python <skrypt>.py --modele ollama:a,ollama:b"
