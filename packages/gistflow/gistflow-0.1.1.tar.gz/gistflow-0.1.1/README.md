# GistFlow

A tiny Python library + CLI for syncing small JSON state via a GitHub Gist.

`gistflow` is useful when you want a cheap, globally reachable state blob over HTTPS
without running your own server. Reads are efficient using HTTP ETags
(`If-None-Match`), so polling is lightweight.

This project intentionally keeps scope small and explicit.

---

## Design goals

- Small and boring
- Explicit configuration
- ETag-aware polling
- No hidden magic

## Non-goals

- Automatic worker discovery
- Strong consistency or atomic multi-writer updates
- High-frequency messaging
- Large payloads

---

## Requirements

- Python 3.9+
- A GitHub account
- A GitHub Personal Access Token with **Gists: read/write**

---

## Installation (development)

```bash
pip install -e .
```
---
## License
MIT
