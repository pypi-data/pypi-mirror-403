[![PyPI version](https://badge.fury.io/py/cro-stem.svg)](https://badge.fury.io/py/cro-stem)
[![Downloads](https://static.pepy.tech/badge/cro-stem)](https://pepy.tech/project/cro-stem)

# Cro-Stem: Lagani hrvatski stemmer

[![Rust](https://img.shields.io/badge/rust-1.x-orange.svg)](https://www.rust-lang.org/)

**Cro-Stem** je brza, lagana i od ovisnosti neovisna Rust biblioteka za stemizaciju hrvatskih riječi. Njegova svrha je svesti inflektirane ili izvedene riječi na njihov korijen, bazu ili osnovni oblik.

Ova biblioteka je dizajnirana za brzinu i minimalnu potrošnju memorije, što je čini idealnom alternativom velikim, resursno intenzivnim AI modelima za zadatke predprocesiranja u obradi prirodnog jezika (NLP), poput indeksiranja pretraga i tekstualne analize.

*Razvio strastveni developer i električar.*

---

## Usporedba: Zašto koristiti `cro-stem`?

| Značajka             | Cro-Stem                                   | Veliki AI modeli (npr. spaCy/CLASSLA) |
| -------------------- | ------------------------------------------ | ------------------------------------- |
| **Veličina**         | < 500KB                                    | ~800MB+                               |
| **Brzina**           | Munjevito brz (tisuće riječi/sek)          | Sporiji, zahtijeva više procesorske snage |
| **Ovisnosti**        | Nula (za CLI) / Minimalne (za Python)      | Mnoge (PyTorch, TensorFlow, itd.)      |
| **Slučaj upotrebe**  | Pretraživanje, Indeksiranje teksta, Osnovni NLP | Potpuna lingvistička analiza, POS tagiranje |

`cro-stem` koristi deterministički algoritam temeljen na pravilima, fokusirajući se na prefikse, sufikse i uobičajene glasovne promjene. Time pruža "dovoljno dobru" točnost stemizacije za većinu aplikacija bez opterećenja neuronske mreže.

## Instalacija

`cro-stem` možete koristiti kao alat naredbenog retka (putem Rust-a) ili kao Python biblioteku.

### Rust / Naredbeni redak

1.  Provjerite imate li instaliran Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2.  Klonirajte repozitorij: `git clone https://github.com/your-username/cro_stem.git`
3.  Izgradite optimiziranu binarnu datoteku: `cd cro_stem && cargo build --release`
4.  Binarna datoteka bit će dostupna na putanji `target/release/cro_stem`.

### Python Biblioteka

1.  Provjerite imate li instaliran Python 3 i `pip`.
2.  Preuzmite najnoviju `.whl` datoteku s [stranice izdanja (Releases)](https://github.com/your-username/cro_stem/releases).
3.  Instalirajte `.whl` datoteku u svoje virtualno okruženje:
    ```sh
    pip install cro_stem-*.whl
    ```

## Upotreba

### Primjer u Rustu

```rust
// Dodajte `cro_stem` u vaš Cargo.toml
// cro_stem = { path = "put/do/cro_stem" }

use cro_stem::CroStem;

fn main() {
    let stemmer = CroStem::new();
    let word = "pjevajući";
    let stem = stemmer.stem(word);
    println!("'{}' -> '{}'", word, stem); // 'pjevajući' -> 'pjev'
}
```

### Primjer u Pythonu

```python
import cro_stem

word = "trčanje"
stem = cro_stem.stem(word)
print(f"'{word}' -> '{stem}'")
# Izlaz: 'trčanje' -> 'trč'

words = ["knjigama", "pjesama", "učenici"]
stems = [cro_stem.stem(w) for w in words]
print(stems)
# Izlaz: ['knjig', 'pjesm', 'učenik']
```

## Licenca

Ovaj projekt je licenciran pod **MIT Licencom**. Detalje potražite u datoteci `LICENSE`.