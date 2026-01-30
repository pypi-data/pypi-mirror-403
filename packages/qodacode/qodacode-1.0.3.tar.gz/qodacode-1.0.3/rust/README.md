# Qodacode Core (Rust Extension)

High-performance core algorithms for the Qodacode security scanner.

## Overview

This module provides compiled, optimized implementations of:

- **Fingerprint Computation**: Stable issue hashing with BLAKE3
- **String Similarity**: Levenshtein distance, homoglyph detection, keyboard proximity
- **Pattern Matching**: Aho-Corasick multi-pattern matching for safe code detection

## Why Rust?

| Aspect | Python | Rust |
|--------|--------|------|
| Speed | 1x | 50-100x |
| Memory | GC overhead | Zero-cost |
| Reverse Engineering | Easy | Difficult |

## Building

### Prerequisites

- Rust toolchain (rustup)
- Python 3.10+
- maturin (`pip install maturin`)

### Development Build

```bash
cd rust
maturin develop
```

### Release Build

```bash
cd rust
maturin build --release
```

### Installing the Wheel

```bash
pip install target/wheels/qodacode_core-*.whl
```

## Usage

```python
from qodacode_core import (
    compute_fingerprint,
    compute_similarity_score,
    is_safe_pattern,
    RUST_CORE_AVAILABLE,
)

# Check if Rust core is available
print(f"Rust core: {RUST_CORE_AVAILABLE}")

# Compute fingerprint
fp = compute_fingerprint("src/config.py", "SEC-001", "api_key = 'secret'")
print(f"Fingerprint: {fp}")

# Check for typosquatting
score = compute_similarity_score("reqeusts", "requests")
print(f"Similarity: {score}")

# Check for safe patterns
is_safe, pattern, reason = is_safe_pattern("key = os.environ['KEY']", "config.py")
print(f"Safe: {is_safe} ({reason})")
```

## Benchmarks

Run benchmarks with:

```bash
cargo bench
```

## Testing

```bash
cargo test
```

## License

Apache-2.0
