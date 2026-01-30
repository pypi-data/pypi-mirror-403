---
description: Testiranje logike stemmera pomoću corpusa
---

Ovaj workflow osigurava da promjene u pravilima ne kvare postojeće testne primjere.

1. Pokreni Rust unit testove:
// turbo
   `cargo test`

2. Ako Rust testovi prolaze, pokreni validaciju protiv `corpus.json`:
   - Koristi `python run_tests.py` (ili ekvivalentnu skriptu).
   - Provjeri mapiranje `original -> expected_stem`.

3. Ako postoji neslaganje, ažuriraj `VOICE_RULES` ili `SUFFIXES` u `lib.rs`.
