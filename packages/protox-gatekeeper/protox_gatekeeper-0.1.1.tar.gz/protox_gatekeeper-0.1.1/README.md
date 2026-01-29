# ProtoX GateKeeper

**ProtoX GateKeeper** is a small, opinionated Python library that enforces
**fail‑closed Tor routing** for HTTP(S) traffic.

The goal is simple:

> If Tor is not active and verified, **nothing runs**.

GateKeeper is designed to be *fire‑and‑forget*: create a client once, then perform network operations with a hard guarantee that traffic exits through the Tor network.

---

## What GateKeeper Is

- A **Tor‑verified HTTP client**
- A thin wrapper around `requests.Session`
- Fail‑closed by default (no silent clearnet fallback)
- Observable (exit IP, optional geo info)
- Suitable for scripts, tooling, and automation

---

## What GateKeeper Is NOT

- ❌ A Tor controller
- ❌ A crawler or scanner
- ❌ An anonymization silver bullet
- ❌ A replacement for Tor Browser

GateKeeper enforces transport routing only. You are still responsible for *what* you do with it.

---

## Requirements

- A locally running Tor client
- SOCKS proxy enabled (default: `127.0.0.1:9150`)

On Windows this usually means **Tor Browser** running in the background.

---

## Installation

### From source (development)

```bash
pip install -e .
```

(Recommended while developing or testing.)

---

## Basic Usage

```python
import logging
from protox_gatekeeper import GateKeeper

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s - %(message)s'
)

gk = GateKeeper(geo=True)

gk.download(
    "https://httpbin.org/bytes/1024",
    "downloads/test.bin"
)
```

### Example output

```
[INFO] gatekeeper.core - Tor verified: 89.xxx.xxx.xxx -> 185.xxx.xxx.xxx
[INFO] gatekeeper.core - Tor exit location: Brandenburg, DE
[INFO] gatekeeper.core - [Tor 185.xxx.xxx.xxx] downloading https://httpbin.org/bytes/1024 -> downloads/test.bin
```

This confirms:
- clearnet IP was measured
- Tor routing was verified
- all traffic used the Tor exit shown

---

## API Overview

### `GateKeeper(...)`

```python
gk = GateKeeper(
    socks_port=9150,
    geo=False
)
```

**Parameters**:
- `socks_port` *(int)* – Tor SOCKS port (default: `9150`)
- `geo` *(bool)* – Enable best‑effort Tor exit geolocation (optional)

Raises `RuntimeError` if Tor routing cannot be verified.

---

### `download(url, target_path)`

Downloads a resource **through the verified Tor session**.

```python
gk.download(url, target_path)
```

- `url` – HTTP(S) URL
- `target_path` – Full local file path (directories created automatically)

---

## Design Principles

- **Fail closed**: no Tor → no execution
- **Single verification point** (during construction)
- **No global state**
- **No logging configuration inside the library**
- **Session reuse without re‑verification**

Logging is emitted by the library, but **configured by the application**.

---

## Logging

GateKeeper uses standard Python logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

The library does **not** call `logging.basicConfig()` internally.

---

## Security Notes

- Tor exit IPs may rotate over time
- Geo information is best‑effort and may be unavailable (rate‑limits, CAPTCHAs)
- GateKeeper guarantees routing, not anonymity

---

## License

MIT License

---

## Status

- Version: **v0.1.1**
- Phase 1 complete
- API intentionally minimal

Future versions may add optional features such as:
- circuit rotation
- ControlPort support
- higher‑level request helpers

Without breaking the core contract.

