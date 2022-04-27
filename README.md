# Projekt ASU - Porządkowanie plików

## Interpretacja zadania

Należy przygotować skrypt w wybranym języku (Python, Per, Bash).

### Funkcjonalności skryptu:
- Jako argumenty podawane są katalogi (X oraz Y)
- Przy pierwszym wykrytym pliku jesteśmy pytani o akcję (wybieramy numer z listy dostępnych opcji)
- Jako argument wybierany jest tryb(y):
  - --find-duplicates
  - --find-temp
  - --find-empty
  - --find-same-name
  - --find-bad-attribute 
  - --find-bad-character
  - --move-to-x/--copy-to-x - Przenieś lub przekopiuj 
- W zależności od wybranego trybu (trybów) wyświetlane są możliwe akcje:
  - na przykład dla trybu find-duplicates po znalezieniu pierwszego pliku wyświetlana jest lista:
    1. usuń plik
    2. pozostaw duplikat
    3. zawsze pozostaw duplikat
    4. usuń losowy 
    5. zawsze usuń losowy
  - natomiast dla trybu find-