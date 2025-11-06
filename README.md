# DropZone
This helper script provides a minimal HTTP endpoint for collecting files from the PromiseCollector app (or any other client) without exposing read access.

## How It Works

| Aspect | Behaviour |
| --- | --- |
| Endpoint | Accepts `POST /upload` with `multipart/form-data` (single `file` part). |
| Storage base | `TARGET_BASE_DIR` environment variable. If unset, uses the script directory. |
| Subdirectory routing | Files ending in `.json`, `.xml`, or `.csv` are stored in `<base>/<UPLOAD_SUBDIR>/` (defaults to `<base>/data/`). Others stay directly under `<base>/`. |
| Size guard | Uploads larger than `MAX_UPLOAD_BYTES` (default 15 MB) are rejected. |
| Read access | All other methods/paths return 404/405 to keep the server write-only. |

## Usage

```bash
# 1. Start the server (adjust env vars as needed)
TARGET_BASE_DIR=/tmp/promise_uploader \
UPLOAD_SUBDIR=ingest \
PORT=9090 \
python3 upload_server.py

# 2. Send a file
curl -F "file=@behavioral_sample.json" http://localhost:9090/upload
```
