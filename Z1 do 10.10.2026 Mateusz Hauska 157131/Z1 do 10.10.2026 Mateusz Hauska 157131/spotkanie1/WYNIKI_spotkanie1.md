# Wyniki: spotkanie 1 (26.09.2026)

Imię i nazwisko: Mateusz Hauska
Model A (API lub lokalny): ollama:llama3.2:3b
Model B: ollama:qwen3:8b

## Ćwiczenie 1.1: porównanie modeli

Przewidywanie przed uruchomieniem (który model wygra w czym i dlaczego): Uważam, że model Llama 3.2:3b będzie generował odpowiedzi szybciej, ponieważ ma mniej parametrów i wymaga mniejszej mocy obliczeniowej. Model Qwen3:8b powinien lepiej poradzić sobie ze streszczeniem, obliczaniem 17%, generowaniem JSON, pytaniami z prawa i reklamacji. Jest większy i może lepiej rozumieć trudniejsze polecenia. Uważam, że Qwen3 8B lepiej streści tekst po polsku, ponieważ jest większym modelem i powinien lepiej rozumieć treść polecenia, Qwen3 8B poprawnie wskaże, że termin 14 dni dotyczy dni kalendarzowych,  Llama 3.2 3B może popełnić błąd, Qwen3 8B będzie 5 razy wolniejszy od Llama 3.2:3B ze względu na większą liczbę parametrów. Obydwa modele powinny poradzić sobie z prostymi zadaniami ale Qwen3:8b udzieli dokładniejszych odpowiedzi. 

| Prompt         | A: czas [s] | A: tokeny we/wy | A: ocena 0–2 | B: czas [s] | B: tokeny we/wy | B: ocena 0–2 |
|---             |---          |---              |---           |---          |---              |---           |
| 1 streszczenie |       3,35  |    64/34        |        1     |      8.29   |      48/435     |       2      |
| 2 obliczenie 17% |     0.22  |    45/41        |        2     |      10.15  |      34/1088    |       2      | 
| 3 JSON         |       0.84  |    57/180       |        2     |      3.53   |      40/374     |       2      | 
| 4 prawo konsumenckie | 0.16  |    58/27        |        0     |      8.54   |      43/916     |       1      |
| 5 odmowa reklamacji |  0.41  |    58/85        |        1     |      1.87   |      43/194     |       1      |        
| Suma ocen:                                     |       6/10   |                               |      8/10    |

model               mediana_s  max_s  tokeny_we  tokeny_wy
------------------  ---------  -----  ---------  ---------
ollama:llama3.2:3b  0,41       3,35   282        367      
ollama:qwen3:8b     8,29       10,15  208        3007  

Ocena: Oba modele otrzymały po 2 punkty za poprawne obliczenie 17% i odczytanie danych do JSON, natomiast Llama otrzymała 1 punkt za streszczenie, ponieważ zamiast streścić tekst przetłumaczyła go na angielski, a Qwen otrzymał 2 punkty za poprawną odpowiedź. W pytaniu o prawo konsumenckie Llama otrzymała 0 punktów za błędną informację, a Qwen 1 punkt za poprawną odpowiedź z błędami. Za odmowę reklamacji oba modele otrzymały po 1 punkcie ze względu na brak uwzględnienia kwestii prawnych.

Rekomendacja (3 zdania, z odwołaniem do liczb): Model Llama3.2:3b był znacznie szybszy osiągając mediana_s 0,41, natomiast Qwen3:8b uzyskał 8.29. Najwyższy czas dla Llama3.2:3b to 3.35, natomiast dla Qwen3:8b to 10.15. Pod względem odpowiedzi lepiej wypada Qwen3:8b zdobywając 8/10, tymczasem Llama3.2:3b dostaje 6/10. Llama3.2:3B zużył  282 tokeny wejściowe i 367 wyjściowych,  Qwen3:8B zużył 208 tokenów wejściowych i  3007 wyjściowych. Qwen3b:8 wygenerował 8 razy więcej tokenów wyjściowych co przełożylo się na dłuższy czas odpowiedzi. Dla trudnych i złożonych odpowiedzi wybrałbym model Qwen3:8b, a dla prostych zadań gdzie jest ważna szybkość i mniejsze zużycie zasobów Llama3.2:3b. Mniejszy model odpowie pewnie i niedokońca prawidłowo

## Z1: temperatura, tokeny, koszt

Wklej wynik skryptu `s1_z1_temperatura_tokeny.py`:

``````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````
Model: ollama:llama3.2:3b

=== ZADANIE Z1 (5 pkt, termin 10.10.2026): temperatura, tokeny i koszt ===
    model: ollama:llama3.2:3b    embeddingi: ollama:bge-m3

Model: ollama:llama3.2:3b

Temperatura 0: 1 różne odpowiedzi na 5 wywołań: {'Vitalis C.'}
Temperatura 1: 5 różne odpowiedzi na 5 wywołań: {'Vitalix.', 'Vitaminox.', 'Vitacell.', 'Vitacel.', 'Vitacelera'}

Tokeny wejściowe PL: 55, EN: 42, różnica: +31%

Koszt 10 000 zapytań (400 tokenów we, 200 wy), tańszy model:  14.00 USD
Koszt 10 000 zapytań (400 tokenów we, 200 wy), droższy model: 70.00 USD
``````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````
Model: ollama:llama3.2:3b.
Przy temperaturze 0 otrzymałem 1 różną odpowiedź na 5 wywołań: Vitalis C.
Przy temperaturze 1 otrzymałem 5 różnych odpowiedzi na 5 wywołań: Vitalix, Vitaminox, Vitacell, Vitacel, Vitacelera
Przy każdym uruchomieniu skryptu przy temperaturze 1 są inne odpowiedzi.
Tokeny wejściowe dla języka polskiego to 55
Tokeny wejściowe dla języka angielskiego to 42. 
Tekst polski wymagał 13 tokenów więcej.

=== AUTOMATYCZNY TEST UCINANIA ZDANIA ===

=== LIMIT: 10 TOKENÓW ===
Odpowiedź: Witamina C jest popularnym składn
Tokeny wyjściowe: 10
Czy odpowiedź została ucięta w połowie zdania? TAK
Znaleziony limit: 10 tokenów

Znalazłem wartość 10 tokenów , przy której model uciął odpowiedź przed zakończeniem zdania. Parametr num_predict pozwala kontrolować maksymalną długość odpowiedzi i ograniczać koszty generowania, jednak zbyt niski limit może powodować otrzymywanie niekompletnych tekstów.

=== KOSZT JEDNEGO ZAPYTANIA ===
Odpowiedź modelu: Vitalis C.
Tokeny wejściowe: 49
Tokeny wyjściowe: 6
Łącznie tokenów: 55
=== KOSZT 10 000 ZAPYTAŃ MIESIĘCZNIE ===
Tokeny wejściowe: 490000
Tokeny wyjściowe: 60000
Łącznie tokenów: 550000
Koszt jednego zapytania: 0.00 USD
Koszt 10 000 zapytań: 0.00 USD
Źródło: https://ollama.com/pricing
Data odczytu: 09.10.2026
Uwaga: nie uwzględniono kosztów prądu i sprzętu.

Wykorzystałem lokalny model Llama3.2:3B uruchomiony przez Ollama. Jedno zapytanie zużyło 49 tokenów wejściowych i 6 tokenów wyjściowych, czyli łącznie 55 tokenów. Przy 10 000 zapytań miesięcznie daje to 490 000 tokenów wejściowych i 60 000 wyjściowych, czyli łącznie 550 000 tokenów. Lokalny model Llama3.2:3B pozwala wykonywać zapytania bez opłat za tokeny

Dlaczego polski tekst kosztuje więcej (2 zdania):
Polski tekst zawiera o 31% więcej tokenów niż angielski, czyli w tym przypadku o 13 tokenów więcej, ponieważ tokenizator jest lepiej dostosowany do języka angielskiego. Polskie słowa mają różne formy gramatyczne, przez co mogą być dzielone na więcej tokenów.

Jaką temperaturę ustawisz do ekstrakcji danych z faktur i dlaczego (1 zdanie):
Ustawię temperaturę 0 ponieważ wyniki są powtarzalne a przy temperaturze 1 wyniki są za każdym razem inne, przy ekstrakcji danych i faktur zależy mi na dokładnych i powtarzalnych odpowiedziach.

