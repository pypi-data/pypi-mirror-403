from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from azstoragetorch.io import BlobIO

from .config import get_sas_token, load_settings, normalize_prefix, normalize_sas_token


def _append_sas(url: str, sas_token: str | None) -> str:
    if not sas_token:
        return url
    token = sas_token.lstrip("?")
    parsed = urlparse(url)
    if parsed.query:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{token}"


def blob_url(
    blob_name: str,
    *,
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    use_default_prefix: bool = False,
) -> str:
    if blob_name.startswith("https://"):
        return _append_sas(blob_name, sas_token)
    settings = load_settings()
    account = (account_name or settings.get("account_name", "")).strip()
    container = (container_name or settings.get("container_name", "")).strip()
    if not account:
        raise ValueError(
            "Missing Azure Storage account. Set it in config or AZURE_STORAGE_ACCOUNT."
        )
    if not container:
        raise ValueError("Missing container name. Set it in config or AZURE_BLOB_TUI_CONTAINER.")
    prefix = settings.get("default_prefix", "") if use_default_prefix else ""
    prefix = normalize_prefix(prefix)
    name = blob_name.lstrip("/")
    if prefix:
        name = f"{prefix}{name}"
    url = f"https://{account}.blob.core.windows.net/{container}/{name}"
    token = sas_token or get_sas_token()
    token, _ = normalize_sas_token(token)
    return _append_sas(url, token)


def blob_open(
    blob_name: str,
    mode: Literal["rb", "wb"] = "rb",
    *,
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    use_default_prefix: bool = False,
):
    url = blob_url(
        blob_name,
        account_name=account_name,
        container_name=container_name,
        sas_token=sas_token,
        use_default_prefix=use_default_prefix,
    )
    return BlobIO(url, mode)
