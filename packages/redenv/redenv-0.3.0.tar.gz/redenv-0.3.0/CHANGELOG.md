# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-01-25

### Added

- **Secret Expansion:** Support for `${VAR_NAME}` syntax for referencing other secrets within values.
- **Raw Value Access:** Added `.raw` property to `Secrets` object to access unexpanded values.
- **Recursive Resolution:** Variable expansion supports multi-level recursion with circular dependency detection.

### Changed

- **Safe Access:** Accessing a non-existent secret via `secrets["KEY"]` now returns `None` instead of raising a `KeyError`.
- **Improved Scoping:** `secrets.scope()` now correctly preserves both expanded and raw values in the resulting subset.

## [0.2.0] - 2026-01-22

### Added

- **Synchronous Client:** Added `RedenvSync` for blocking contexts (scripts, legacy apps).
- **Write Support:** Implemented `client.set(key, value)` with full version history management.
- **Smart Secrets Object:**
  - `secrets.get(key, cast=int)`: Auto-convert types.
  - `secrets.scope("PREFIX_")`: Create namespaced configuration subsets.
  - `secrets.require("KEY")`: Fail-fast validation for missing keys.
- **Time Travel:** Added `client.get_version(key, v)` to fetch historical secrets. Supports both absolute IDs and relative indexing (0=Latest, 1=Previous).
- **Security Hardening:** `Secrets` object now masks values (`********`) in logs/print statements to prevent accidental leakage.
- **Override Protection:** Added `env.override` option to prevent overwriting existing environment variables.

## [0.1.0] - 2026-01-22

### Added

- **Initial Release:** First public beta release of the `redenv` Python SDK.
- **Zero-Knowledge Security:** All cryptographic operations (AES-256-GCM, PBKDF2) are performed locally.
- **Async Support:** Built on `asyncio` and `upstash-redis` for high-performance non-blocking operations.
- **SWR Caching:** Implemented a robust `Stale-While-Revalidate` caching strategy using `cachetools.LRUCache`.
- **Environment Injection:** Automatically populates `os.environ` with decrypted secrets on `load()`.