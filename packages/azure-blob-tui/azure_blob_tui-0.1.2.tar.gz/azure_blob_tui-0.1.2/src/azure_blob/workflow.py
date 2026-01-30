from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import BinaryIO

from azure.storage.blob import BlobPrefix, ContainerClient, ContentSettings

from .config import load_settings, normalize_prefix
from .storage import get_container_client


@dataclass(frozen=True)
class BlobContext:
    client: ContainerClient
    account_name: str
    container_name: str
    default_prefix: str = ""

    @classmethod
    def from_config(
        cls,
        *,
        account_name: str | None = None,
        container_name: str | None = None,
        sas_token: str | None = None,
    ) -> BlobContext:
        settings = load_settings()
        account = (account_name or settings.get("account_name", "")).strip()
        container = (container_name or settings.get("container_name", "")).strip()
        default_prefix = settings.get("default_prefix", "")
        client = get_container_client(
            account_name=account or None,
            container_name=container or None,
            sas_token=sas_token,
        )
        return cls(
            client=client,
            account_name=account,
            container_name=container,
            default_prefix=default_prefix,
        )

    def resolve_name(self, blob_name: str, *, use_default_prefix: bool = False) -> str:
        name = blob_name.lstrip("/")
        if use_default_prefix:
            prefix = normalize_prefix(self.default_prefix)
            if prefix and not name.startswith(prefix):
                name = f"{prefix}{name}"
        return name

    def iter_blobs(self, *, prefix: str = "", use_default_prefix: bool = False) -> Iterable[str]:
        name = self.resolve_name(prefix, use_default_prefix=use_default_prefix)
        return (item.name for item in self.client.list_blobs(name_starts_with=name))

    def iter_prefixes(
        self,
        *,
        prefix: str = "",
        delimiter: str = "/",
        use_default_prefix: bool = False,
    ) -> Iterable[str]:
        name = self.resolve_name(prefix, use_default_prefix=use_default_prefix)
        for item in self.client.walk_blobs(name_starts_with=name, delimiter=delimiter):
            if isinstance(item, BlobPrefix):
                yield item.name

    def read_bytes(self, blob_name: str, *, use_default_prefix: bool = False) -> bytes:
        name = self.resolve_name(blob_name, use_default_prefix=use_default_prefix)
        blob = self.client.get_blob_client(name)
        return blob.download_blob().readall()

    def write_bytes(
        self,
        blob_name: str,
        data: bytes | bytearray | BinaryIO,
        *,
        use_default_prefix: bool = False,
        overwrite: bool = True,
        content_type: str | None = None,
    ) -> None:
        name = self.resolve_name(blob_name, use_default_prefix=use_default_prefix)
        blob = self.client.get_blob_client(name)
        content_settings = ContentSettings(content_type=content_type) if content_type else None
        blob.upload_blob(data, overwrite=overwrite, content_settings=content_settings)
