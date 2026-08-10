# FHE Lexicon Freeze

Use this reference with `bilingual_glossary.md`. The glossary maps preferred expressions; this file defines terms whose spelling or semantics may not be varied by language passes.

## Frozen categories

- **Schemes and primitives:** BFV, BGV, CKKS, TFHE, FHEW, and GSW. Preserve established capitalization and hyphenation.
- **Libraries and toolchains:** OpenFHE, Microsoft SEAL, HElib, Lattigo, Concrete, TFHE-rs, and HEaaN.
- **Parameters and symbols:** preserve the chosen symbols and units for ring dimension, plaintext modulus, ciphertext modulus, scale, multiplicative depth, noise budget, and security parameters. Never swap a symbol for prose or prose for a symbol during polishing.
- **Operations:** packing, SIMD slots, rotation, key switching, relinearization, modulus switching, rescaling, and bootstrapping. Bootstrapping has scheme-dependent semantics and is not a free synonym across contexts.
- **Approximation:** retain every precision qualifier attached to CKKS arithmetic, polynomial approximation, decoding error, or empirical tolerance. Never rewrite an approximate result as exact.
- **Security semantics:** freeze `semi-honest`, `malicious`, `honest-but-curious`, `selective`, `adaptive`, `IND-CPA`, `IND-CCA`, `leveled`, `fully homomorphic`, `computational`, `statistical`, `static corruption`, and `adaptive corruption`. Do not broaden, narrow, omit, or exchange bounded leakage descriptions.

Security semantics have the highest priority in the immutable set. A style preference cannot override them.

## Common misuse table

| Incorrect | Correct | Why reviewers care |
|---|---|---|
| full homomorphic encryption | fully homomorphic encryption | The standard name signals technical literacy. |
| Open FHE | OpenFHE | Product and library names are identifiers, not prose variants. |
| SEAL | Microsoft SEAL, then SEAL if defined | The first use should identify the toolchain unambiguously. |
| HE Lib | HElib | Incorrect spelling impedes reproducibility and search. |
| TFHE rs | TFHE-rs | The official project name must remain stable. |
| ciphertext, encrypted value, and encoding used interchangeably | the project-defined term for each object | These objects can occupy different layers of the construction. |
| exact CKKS result | approximate CKKS result with its precision scope | CKKS does not justify exact-arithmetic wording. |
| rotation means data movement at no cost | rotation with its key-switching and runtime cost | The omitted operation may dominate the system cost. |
| rescaling used as a synonym for modulus switching | the scheme-appropriate operation | Their purposes and scale effects differ by scheme. |
| bootstrapping used without scheme context | the defined refresh or scheme-switching operation | The operation and guarantee are not uniform across schemes. |
| semi-honest replaced by malicious | retain the proven adversary model | The replacement asserts a stronger security result. |
| honest-but-curious silently removed | retain or formally redefine the adversary assumption | Omission hides a limitation in the threat model. |
| selective security rewritten as adaptive security | retain selective security | The notions have different quantifier order and strength. |
| IND-CPA rewritten as IND-CCA | retain the proved notion | The stronger notion requires different evidence. |
| leveled HE rewritten as FHE | retain leveled HE unless bootstrapping supports the claim | Supported circuit depth is part of the construction's scope. |
| computational privacy rewritten as statistical privacy | retain the demonstrated guarantee | The assumptions and strength are different. |
| bounded access-pattern leakage rewritten as privacy | state the exact leakage boundary | A reviewer needs the observable information, not a blanket label. |

When a project adopts a narrower spelling or symbol convention, record it in the project glossary. Do not duplicate the bilingual mappings here.
