---
description: Inicijalizacija SerbStem projekta (Rust + Python + WASM)
---

Ovaj workflow postavlja osnovnu strukturu projekta temeljenu na CroStem arhitekturi.

1. Kreiraj `Cargo.toml` s potrebnim dependencijima (`pyo3`, `wasm-bindgen`, `lazy_static`).
2. Kreiraj `pyproject.toml` za Maturin (Python bindings).
3. Postavi `src/lib.rs` s osnovnim strukturama za `Aggressive` i `Conservative` modove.
4. Kreiraj osnovni `corpus.json` za testiranje.

// turbo
5. Pokreni `cargo fetch` za provjeru dependencija.
