---
description: Build i pakiranje SerbStem-a za Python i WASM
---

Ovaj workflow opisuje korake za generiranje distribucijskih paketa.

1. **Python Build**:
// turbo
   `maturin build --release` - Generira wheel datoteku u `target/wheels`.

2. **WASM Build**:
// turbo
   `wasm-pack build --target web` - Generira JS/WASM paket u `pkg/` folderu.

3. Provjeri generirane artefakte i ažuriraj verziju u `Cargo.toml` ako je potrebno.
