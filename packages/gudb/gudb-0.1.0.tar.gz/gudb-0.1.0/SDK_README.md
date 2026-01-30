# gudb: The Database Seatbelt 🛡️

**gudb** is a high-performance database safety layer designed to prevent production disasters *before* they happen. It acts as a "seatbelt" for your data, intercepting dangerous queries at the driver level with zero-latency heuristics and Senior DRE-level AI advice.

## ✨ Why a Seatbelt?
- **Zero-Latency Protection**: Local heuristics block `DELETE` or `DROP` without `WHERE` in <1ms.
- **Fail-Safe by Design**: If the AI or network is down, the seatbelt stays on.
- **AI Advisor**: Deep query analysis and optimization tips provided by Gemini AI.
- **Driver-Level Hook**: Drops into your `psycopg2` connection in one line of code.
- **Privacy First**: SQL redaction ensures sensitive PII never leaves your network.

## 📦 Installation

```bash
pip install gudb
```

To install with framework-specific extras:
```bash
pip install "gudb[fastapi]"
```

## 🚀 Quick Start

### 1. The One-Liner (DB Driver Level)
Wrap your database connection to start guarding immediately.

```python
import psycopg2
from gudb import monitor

# Create your connection
raw_conn = psycopg2.connect("postgres://...")

# --- GUARD IT ---
conn = monitor(raw_conn)
# -----------------

cur = conn.cursor()
cur.execute("DELETE FROM orders;") # 🛑 Raises DisasterBlockedError
```

### 2. FastAPI Integration
```python
from fastapi import FastAPI
from gudb.middlewares.fastapi import SafeDBMiddleware

app = FastAPI()
app.add_middleware(SafeDBMiddleware)
```

## ⚙️ Configuration
The SDK can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GUDB_API_ENDPOINT` | The evaluation backend URL | `https://ai-db-sentinel.onrender.com/api/sdk/evaluate` |
| `GUDB_ENVIRONMENT`  | `prod`, `stage`, or `dev` | `production` |
| `GUDB_FAIL_OPEN`    | Allow queries if AI is down | `True` |
| `GUDB_REDACT_PII`   | Scrub SQL literals | `True` |

## 🛠️ Advanced Usage (Extensibility)
You can implement your own AI provider if you want to use a local model or a different API.

```python
from gudb.providers.base import BaseProvider
from gudb import Gudb

class MyCustomProvider(BaseProvider):
    def evaluate(self, query, context):
        if "DROP" in query.upper():
            return {"verdict": "STOP", "issue": "No drops allowed"}
        return {"verdict": "GO"}

# Initialize with custom provider
gudb = Gudb(provider=MyCustomProvider())
```

## 🏗️ Development & Publishing
To test locally:
```bash
pip install -e .[dev]
pytest tests/
```

To publish to PyPI:
```bash
python -m build
twine upload dist/*
```

---
Built with ❤️ by the gudb Team. Ensuring your database sleeps soundly.
