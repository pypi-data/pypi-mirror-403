import random
class Szyfr:
    def __init__(self, słowo_klucz, alfabet="ABCDEFGHIJKLMNOPRSTUWYZ", debug=False): 
        self.debug = debug
        # Szybki test musi być uruchomiany od razu po debug - inaczej nadpisze alfabet, słowo_klucz i tabelę
        self.szybki_test() 
        self.alfabet = alfabet
        self.słowo_klucz = słowo_klucz
        self.tabela = self.utworz_tabele(słowo_klucz)
        self.test_tabeli()
        

    """
    Tworzy dwuwymiarową tablice zgodnie z założeniami tabeli opisanymi w krokach 1, 2, 3 i 4
    Potrzebna na potrzeby późniejszych operacji takich jak szyfrowanie czy odszyfrowanie 
    Zwraca tą tablice (w formie znaków w listach w liście).
    Przykład:
    Wejście: 
    "KAROLINKA"
    Wyjście:
    [ 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 
        ['R', 'S', 'T', 'U', 'W', 'Y', 'Z', 'A', 'B'], 
        ['O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y', 'Z'], 
        ['L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U'], 
        ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R'], 
        ['N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y'], 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], 
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    ]
    """
    def utworz_tabele(self, słowo_klucz: str):
        # Etap 1 i 2
        tabela = [["" for y in range(len(słowo_klucz))] for x in range(len(słowo_klucz))]

        # Etap 3
        for numer_wiersza in range(len(słowo_klucz)):
            tabela[numer_wiersza][0] = słowo_klucz[numer_wiersza]

        # Etap 4
        for numer_wiersza in range(len(słowo_klucz)):
            pozycja_w_alfabecie = self.alfabet.find(słowo_klucz[numer_wiersza][0])

            for numer_kolumny in range(len(tabela[numer_wiersza])):
                tabela[numer_wiersza][numer_kolumny] = self.alfabet[pozycja_w_alfabecie]
                pozycja_w_alfabecie += 1

                # Zabezpieczenie przed przepełnieniem
                if pozycja_w_alfabecie > (len(self.alfabet)-1):
                    pozycja_w_alfabecie = 0
            
        return tabela


    """
    Przeszukuje tablice dwuwymiarową, 
    wygenerowaną wcześniej przez funkcję utworz_tabele w poszukiwaniu pozycji danej litery w tej tabeli.
    Zwraca rzeczywiste (czyli zaczynac liczyć od 1) pozycje tabel w formie listy krotek. 
    Pierwszy element krotki oznacza kolumnę, drugi wiersz.
    Przykład:
    Wejście:
    "H",
    [ 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 
        ['R', 'S', 'T', 'U', 'W', 'Y', 'Z', 'A', 'B'], 
        ['O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y', 'Z'], 
        ['L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U'], 
        ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R'], 
        ['N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y'], 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], 
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    ]
    Wyjście:
    [
        (8, 2),
        (8, 9)
    ]
    """
    def znajdz_wszystkie_pozycje(self, litera: str):
        tabela = self.tabela
        pozycje_w_tabeli = []
        for numer_wiersza in range(len(tabela)):
            for numer_kolumny in range(len(tabela[numer_wiersza])):
                if tabela[numer_wiersza][numer_kolumny] == litera:
                    pozycje_w_tabeli.append((numer_kolumny+1, numer_wiersza+1))
        return pozycje_w_tabeli


    """
    Szyfruje tekst_do_zaszyfrowania zgodnie z założeniami.
    Nie wymaga obiektu wygenerowanego przez funkcję utworz_tabele,
    ale funkcja zależna znajdz_wszystkie_pozycje już tego obiektu wymaga.
    Słowem nadal jest potrzebny ten obiekt.
    Zwraca zaszyfrowany tekst zgodnie z założeniami.
    Wejście:
    "HARCERZ I HARCERKA",
    [ 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 
        ['R', 'S', 'T', 'U', 'W', 'Y', 'Z', 'A', 'B'], 
        ['O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y', 'Z'], 
        ['L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U'], 
        ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R'], 
        ['N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y'], 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], 
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    ]
    Wyjście:
    "8x2 1x9 7x8 3x9 5x9 7x1 7x3\t9x9\t8x2 8x3 7x1 3x9 5x9 1x3 1x1 1x2"
    """
    def szyfruj(self, tekst_do_zaszyfrowania: str):
        tekst_do_zaszyfrowania = tekst_do_zaszyfrowania.upper()
        tekst_do_zaszyfrowania = tekst_do_zaszyfrowania.replace("\n", " ")
        zaszyfrowany_tekst = ""
        słowa = tekst_do_zaszyfrowania.split()
        numer_słowa = 0
        for słowo in słowa:
            numer_znaku = 0
            for znak in słowo:
                wszystkie_pozycje = self.znajdz_wszystkie_pozycje(znak)
                if len(wszystkie_pozycje) == 0:
                    if self.debug:
                        print("Test tekstu do zaszyfrowania: Not OK!")
                        print("Słowo klucz:")
                        print(repr(self.słowo_klucz))
                        print("Tabela:")
                        [print(x) for x in self.tabela]
                        print("Tekst do zaszyfrowania:")
                        print(repr(tekst_do_zaszyfrowania))
                    raise Exception(f'Błąd szyfrowanej wiadomości. Znak "{repr(znak)}" nie znajduje się w podanym alfabecie. Usuń/zmień ten znak lub dodaj go do alfabetu.')
                kolumna, wiersz = random.choice(wszystkie_pozycje)
                zaszyfrowany_tekst += f"{kolumna}x{wiersz}"
                # Dodawanie spacji pomiędzy znakami (oprócz ostatniego)
                if numer_znaku != (len(słowo)-1):
                    zaszyfrowany_tekst += " "
                numer_znaku += 1
            # Dodawanie tabulatora pomiędzy słowami (oprócz ostatniego)
            if numer_słowa != (len(słowa)-1):
                    zaszyfrowany_tekst += "\t"
            numer_słowa += 1
        if self.debug:
            print("Test tekstu do zaszyfrowania: OK")
        return zaszyfrowany_tekst

    """
    Odszyfrowuje tekst_do_odszyfrowania zgodnie z założeniami.
    Wymaga obiektu wygenerowanego przez funkcję utworz_tabele.
    Zwraca odszyfrowany tekst zgodnie z założeniami.
    Wejście:
    "8x2 1x9 7x8 3x9 5x9 7x1 7x3\t9x9\t8x2 8x3 7x1 3x9 5x9 1x3 1x1 1x2",
    [ 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 
        ['R', 'S', 'T', 'U', 'W', 'Y', 'Z', 'A', 'B'], 
        ['O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y', 'Z'], 
        ['L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U'], 
        ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R'], 
        ['N', 'O', 'P', 'R', 'S', 'T', 'U', 'W', 'Y'], 
        ['K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T'], 
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    ]
    Wyjście:
    "HARCERZ I HARCERKA"
    """
    def odszyfruj(self, tekst_do_odszyfrowania: str):
        tabela = self.tabela
        odszyfrowany_tekst = ""
        wyrazy = tekst_do_odszyfrowania.split("\t")
        numer_wyrazu = 0
        for wyraz in wyrazy:
            litery = wyraz.split()
            for litera in litery:
                kolumna, wiersz = litera.split("x")
                kolumna = int(kolumna)
                wiersz = int(wiersz)
                if kolumna > len(self.słowo_klucz) or wiersz > len(self.słowo_klucz):
                    if self.debug:
                        print("Test tekstu do odszyfrowania: Not OK!")
                        print("Słowo klucz:")
                        print(repr(self.słowo_klucz))
                        print("Tabela:")
                        [print(x) for x in self.tabela]
                        print("Tekst do odszyfrowania:")
                        print(repr(tekst_do_odszyfrowania))
                    raise Exception("Błąd zaszyfrowanej wiadomości. Zaszyfrowana wiadomość na 120% nie jest zaszyfrowana tym słowem klucz.")
                odszyfrowany_tekst += tabela[wiersz-1][kolumna-1]
            if numer_wyrazu != (len(wyrazy)-1):
                    odszyfrowany_tekst += " "
            numer_wyrazu += 1
        if self.debug:
            print("Test tekstu do odszyfrowania: OK")
        return odszyfrowany_tekst
    
    """
    Testuje poprawność wykonywania się kodu w danych warunkach (test syntetyczny)
    """
    def szybki_test(self):
        self.alfabet = "ABCDEFGHIJKLMNOPRSTUWYZ"
        self.słowo_klucz = "KAROLINKA"
        self.tabela = self.utworz_tabele(self.słowo_klucz)
        if self.odszyfruj(self.szyfruj("HARCERZ I HARCERKA")) == "HARCERZ I HARCERKA":
            if self.debug:
                print("Szybki test: OK")
        else:
            if self.debug:
                print("Szybki test: Not OK!")
                print("Słowo klucz:")
                print(repr(self.słowo_klucz))
                print("Tabela:")
                [print(x) for x in self.tabela]
                print("Zaszyfrowany tekst HARCERZ I HARCERKA:")
                test = self.szyfruj("HARCERZ I HARCERKA")
                print(repr(test))
                print("Odszyfrowany tekst powyżej:")
                print(self.odszyfruj(test))
            raise Exception("Szybki test się nie powiódł! Program nie działa prawidłowo! Zabraniam użycia do momentu naprawy!")

    """
    Testuje czy tabela wypełnia cały alfabet
    """
    def test_tabeli(self):
        for litera in self.alfabet:
            if len(self.znajdz_wszystkie_pozycje(litera)) == 0:
                if self.debug:
                    print("Test tabeli: Not OK!")
                    print("Słowo klucz:")
                    print(repr(self.słowo_klucz))
                    print("Tabela:")
                    [print(x) for x in self.tabela]
                raise Exception("Test tabeli się nie powiódł! Słowo klucz którego użyłeś nie wypełnia całego alfabetu. Użyj dłuższego słowa klucz lub innego alfabetu.")
        if self.debug:
            print("Test tabeli: OK")
               
# TESTY
testowy_obiekt = Szyfr("KAROLINKA", debug = False)

# TEST 1
if testowy_obiekt.odszyfruj(testowy_obiekt.szyfruj("HARCERZ I HARCERKA")) == "HARCERZ I HARCERKA":
    if testowy_obiekt.debug:
        print("Test 1: OK")
else:
    if testowy_obiekt.debug:
        print("Test 1: Not OK!")
        print("Słowo klucz:")
        print(repr(testowy_obiekt.słowo_klucz))
        print("Tabela:")
        [print(x) for x in testowy_obiekt.tabela]
        print("Zaszyfrowany tekst HARCERZ I HARCERKA:")
        test = testowy_obiekt.szyfruj("HARCERZ I HARCERKA")
        print(repr(test))
        print("Odszyfrowany tekst powyżej:")
        print(testowy_obiekt.odszyfruj(test))
    raise Exception("Test 1 się nie powiódł! Program nie działa prawidłowo! Zabraniam użycia do momentu naprawy!")



