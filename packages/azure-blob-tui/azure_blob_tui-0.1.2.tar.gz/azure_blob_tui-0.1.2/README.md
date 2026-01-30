# azure-blob-tui

Terminal TUI for browsing Azure Blob Storage, plus Python helpers to read/write blobs
directly from your training code (no local files required).

## First-time setup

Run the TUI once to configure account/container/prefix and (optionally) store SAS
in an encrypted local file. On later runs, if SAS is stored, you only need the
passphrase (no need to re-enter SAS).

```bash
azure-blob-tui --configure
```

During first run you will be prompted for:

- account name / container name / default prefix
- whether to store SAS in an encrypted local file
- (if yes) the SAS token and a passphrase to encrypt it

Later runs:

- If SAS is stored, you will only be prompted for the passphrase.
- If you set `AZURE_BLOB_TUI_PASSPHRASE`, no prompt is needed.

## Use the TUI

```bash
azure-blob-tui
```

## Reconfigure

```bash
azure-blob-tui --configure
```

## Python API (no local files)

All helpers use the same config (account/container/default prefix) and SAS token
stored by `azure-blob-tui --configure`. If `AZURE_BLOB_TUI_PASSPHRASE` is set,
no prompt is needed.

Default prefix behavior:

- Default prefix is **not** applied automatically.
- Pass `use_default_prefix=True` to opt in per call.

### blob_open (file-like stream)

```python
import torch
from azure_blob import blob_open

# Save directly to Blob
with blob_open("checkpoints/step-100/model.pt", "wb") as f:
    torch.save(model.state_dict(), f)

# Load directly from Blob
with blob_open("checkpoints/step-100/model.pt", "rb") as f:
    state = torch.load(f, weights_only=False)
```

### Save JSON/YAML/text to Blob

```python
import io
import json
from azure_blob import blob_open

with blob_open("artifacts/config.json", "wb") as raw:
    with io.TextIOWrapper(raw, encoding="utf-8") as f:
        json.dump({"lr": 1e-4}, f)
```

### blob_url (signed URL helper)

```python
from azure_blob import blob_url

url = blob_url("images/cat.png")
```

### Storage helpers

```python
from azure_blob import (
    download_dir,
    download_file,
    list_blobs,
    upload_dir,
    upload_file,
)

upload_file("local.txt", "artifacts/local.txt")
download_file("artifacts/local.txt", "local_copy.txt")

for name in list_blobs(prefix="artifacts/"):
    print(name)
```

### BlobContext (high-level workflow helper)

`BlobContext` wraps a configured `ContainerClient` and adds convenience helpers
for prefix resolution, listing, and in-memory read/write.

```python
import os
from azure_blob import BlobContext

os.environ["AZURE_BLOB_TUI_PASSPHRASE"] = "your-passphrase"

ctx = BlobContext.from_config()

for prefix in ctx.iter_prefixes(prefix="overview/among/"):
    print(prefix)

data = ctx.read_bytes("overview/among/123/topdown.png")
ctx.write_bytes(
    "overview/among/123/processed.png",
    data,
    content_type="image/png",
)
```

## Choosing the right helper

- `BlobContext`: best for workflows that need listing, grouping, and in-memory
    read/write without touching disk.
- `blob_open`: best for file-like streaming APIs (e.g., `torch.save/load`,
    `TextIOWrapper`, or very large files).
- `read_bytes`/`write_bytes`: best for small-to-medium blobs where a full in-memory
    buffer is fine (images, JSON, etc.).
- `list_blobs`/`iter_prefixes`: best for enumeration and directory-like traversal.
- `download_*`/`upload_*`: local file paths (avoid these if you want no local storage).

## Notes

- SAS tokens are not stored in the config file, but in an encrypted local file.
- `blob_open` works for any file type (torch checkpoints, JSON, YAML, text, etc.).
