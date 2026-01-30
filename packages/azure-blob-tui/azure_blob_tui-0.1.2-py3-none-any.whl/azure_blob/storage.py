from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from azure.storage.blob import ContainerClient

from .config import get_sas_token, load_settings, normalize_prefix, normalize_sas_token


def _resolve_settings(
    account_name: str | None,
    container_name: str | None,
    sas_token: str | None,
) -> tuple[str, str, str | None]:
    settings = load_settings()
    account = (account_name or settings.get("account_name", "")).strip()
    container = (container_name or settings.get("container_name", "")).strip()
    sas = (sas_token or get_sas_token()).strip()
    sas, account_from_url = normalize_sas_token(sas)
    if account_from_url:
        account = account_from_url
    sas = sas or None
    if not account:
        raise ValueError(
            "Missing Azure Storage account. Set it in config or AZURE_STORAGE_ACCOUNT."
        )
    if not container:
        raise ValueError("Missing container name. Set it in config or AZURE_BLOB_TUI_CONTAINER.")
    return account, container, sas


def get_container_client(
    *,
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
) -> ContainerClient:
    account, container, sas = _resolve_settings(account_name, container_name, sas_token)
    account_url = f"https://{account}.blob.core.windows.net"
    return ContainerClient(account_url, container, credential=sas)


def upload_file(
    local_path: str | Path,
    blob_name: str,
    *,
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    overwrite: bool = True,
) -> None:
    client = get_container_client(
        account_name=account_name, container_name=container_name, sas_token=sas_token
    )
    blob = client.get_blob_client(blob_name)
    with open(Path(local_path), "rb") as handle:
        blob.upload_blob(handle, overwrite=overwrite)


def download_file(
    blob_name: str,
    local_path: str | Path,
    *,
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    overwrite: bool = True,
) -> None:
    client = get_container_client(
        account_name=account_name, container_name=container_name, sas_token=sas_token
    )
    target = Path(local_path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"{target} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = client.get_blob_client(blob_name)
    stream = blob.download_blob()
    data = stream.readall()
    target.write_bytes(data if isinstance(data, bytes) else data.encode())


def upload_dir(
    local_dir: str | Path,
    *,
    prefix: str = "",
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    overwrite: bool = True,
) -> int:
    client = get_container_client(
        account_name=account_name, container_name=container_name, sas_token=sas_token
    )
    root = Path(local_dir)
    prefix = normalize_prefix(prefix)
    uploaded = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        blob_name = f"{prefix}{rel}" if prefix else rel
        with open(path, "rb") as handle:
            client.upload_blob(name=blob_name, data=handle.read(), overwrite=overwrite)
        uploaded += 1
    return uploaded


def download_dir(
    local_dir: str | Path,
    *,
    prefix: str = "",
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
    overwrite: bool = True,
) -> int:
    client = get_container_client(
        account_name=account_name, container_name=container_name, sas_token=sas_token
    )
    root = Path(local_dir)
    prefix = normalize_prefix(prefix)
    downloaded = 0
    blobs = client.list_blobs(name_starts_with=prefix)
    for blob in blobs:
        name = blob.name
        if prefix:
            if not name.startswith(prefix):
                continue
            rel = name[len(prefix) :]
        else:
            rel = name
        if not rel or rel.endswith("/"):
            continue
        target = root / rel
        if target.exists() and not overwrite:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        stream = client.download_blob(name)
        data = stream.readall()
        target.write_bytes(data if isinstance(data, bytes) else data.encode())
        downloaded += 1
    return downloaded


def list_blobs(
    *,
    prefix: str = "",
    account_name: str | None = None,
    container_name: str | None = None,
    sas_token: str | None = None,
) -> Iterable[str]:
    client = get_container_client(
        account_name=account_name, container_name=container_name, sas_token=sas_token
    )
    prefix = normalize_prefix(prefix)
    return (item.name for item in client.list_blobs(name_starts_with=prefix))
