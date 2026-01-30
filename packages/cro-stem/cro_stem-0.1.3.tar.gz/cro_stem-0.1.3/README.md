# Cro-Stem: Munjevit Hrvatski Stemmer 🚀🇭🇷

[![PyPI version](https://badge.fury.io/py/cro-stem.svg)](https://badge.fury.io/py/cro-stem)
[![Downloads](https://static.pepy.tech/badge/cro-stem)](https://pepy.tech/project/cro-stem)
[![Rust](https://img.shields.io/badge/rust-1.x-orange.svg)](https://www.rust-lang.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**Cro-Stem** je moderna, munjevit brz Rust biblioteka za morfološku normalizaciju (stemming) hrvatskog jezika. S točnošću od **>91%**, idealna je zamjena za spore i teške AI modele u produkcijskim sustavima.

> 🏆 **Novo u v0.1.3:** Uveden `StemMode` (Agresivni/Konzervativni mod) i postignuta točnost od 91.4% na testnom korpusu od 1000 riječi.

## ✨ Ključne Značajke

*   **⚡ Munjevita brzina:** Napisan u Rustu, obrađuje milijune riječi u sekundi.
*   **🎯 Visoka točnost:** **91.4%** na korpusu od 1000 riječi (nadmašuje većinu rule-based alata).
*   **🎛️ Dualni Mod Rada:**
    *   `Aggressive`: Za tražilice (Elasticsearch, Solr) - reže do korijena (`knjigama` -> `knjig`).
    *   `Conservative`: Za NLP analizu - čuva lemu (`knjigama` -> `knjiga`).
*   **📦 Zero-Dependency:** Nema teških ovisnosti (PyTorch, TensorFlow). Samo 500KB.
*   **🐍 Python Bindings:** Jednostavna `pip install` integracija.

## 🚀 Usporedba

| Značajka | Cro-Stem v0.1.3 | Veliki AI Modeli (spaCy/CLASSLA) |
| :--- | :--- | :--- |
| **Veličina** | **< 0.5 MB** | ~800 MB+ |
| **Brzina** | **>1M riječi/sek** | ~10k riječi/sek |
| **Stemming Točnost** | **~91.4%** | ~95-97% |
| **Infrastruktura** | Običan CPU / Raspberry Pi | GPU preporučljiv |
| **Upotreba** | Search, Indexing, High-load | Deep Semantic Analysis |

## 🛠️ Instalacija

### Python
```bash
pip install cro-stem
```

### Rust
U vašem `Cargo.toml`:
```toml
[dependencies]
cro_stem = "0.1.3"
```

## 📖 Korištenje

### Rust
```rust
use cro_stem::{CroStem, StemMode};

fn main() {
    // Odaberite mod: Aggressive (za search) ili Conservative (za lingvistiku)
    let stemmer = CroStem::new(StemMode::Aggressive);
    
    let words = vec!["učiteljice", "najljepših", "crveniji"];
    for w in words {
        println!("{} -> {}", w, stemmer.stem(w));
    }
    // Izlaz (Aggressive):
    // učiteljice -> učitelj
    // najljepših -> ljep
    // crveniji -> crven
}
```

### Python
```python
import cro_stem

# Default je Agresivni mod (najbolji za pretragu)
print(cro_stem.stem("pjevajući")) 
# 'pjev'

# Za buduće verzije planiramo exposeati modove i kroz Python API
words = ["kućama", "stolovima", "čovjekom"]
stems = [cro_stem.stem(w) for w in words]
print(stems)
# ['kuć', 'stol', 'čovjek']
```

## 📜 Licenca

Ovaj projekt je licenciran pod **GNU Affero General Public License v3.0 (AGPL-3.0)**.

To znači:
*   ✅ **Slobodno korištenje:** Možete ga koristiti, mijenjati i dijeliti besplatno u svojim **Open Source** projektima (pod uvjetom da i oni koriste AGPL/GPL kompatibilnu licencu).
*   ❌ **Zatvoreni kod:** Ako planirate koristiti `CroStem` u komercijalnom softveru zatvorenog koda (gdje ne želite dijeliti svoj izvorni kod), **ova licenca to ne dopušta** bez otvaranja vašeg koda.

💡 **Komercijalna licenca:**
Za upotrebu u zatvorenim (proprietary) sustavima bez obveze dijeljenja koda, molimo kontaktirajte autora za kupnju **Komercijalne (Enterprise) licence** koja vas oslobađa AGPL obveza.
**. Detalje potražite u datoteci `LICENSE`.