#!/usr/bin/env python3
"""
Terminal TUI for browsing Azure Blob Storage with SAS auth.
"""

from __future__ import annotations

import argparse
import os
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobPrefix, ContainerClient
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView, Static

from .config import (
    ACCOUNT_NAME,
    CONTAINER_NAME,
    DEFAULT_PREFIX,
    LOCK_TO_DEFAULT_PREFIX,
    ensure_env,
    load_settings,
    normalize_prefix,
)


@dataclass(frozen=True)
class Entry:
    full_name: str
    display: str
    is_dir: bool
    size: int | None = None


class PromptScreen(ModalScreen[str | None]):
    DEFAULT_CSS = """
    PromptScreen {
        align: center middle;
        width: 100%;
        height: 100%;
        background: #f2f2f2 70%;
    }
    .prompt {
        width: 72%;
        padding: 1 2;
        border: tall #cfcfcf;
        background: #ffffff;
    }
    .prompt_title {
        text-style: bold;
        margin-bottom: 1;
    }
    .prompt_hint {
        color: #666666;
        margin-top: 1;
    }
    Input {
        background: #ffffff;
        color: #222222;
        border: tall #cfcfcf;
        padding: 0 1;
    }
    #prompt_input {
        background: #ffffff;
        color: #222222;
        border: tall #cfcfcf;
    }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, placeholder: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._title, classes="prompt_title"),
            Input(placeholder=self._placeholder, id="prompt_input"),
            Static("Enter=OK  Esc=Cancel", classes="prompt_hint"),
            classes="prompt",
        )

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


class MessageScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    MessageScreen {
        align: center middle;
        width: 100%;
        height: 100%;
        background: #f2f2f2 70%;
    }
    .message {
        width: 80%;
        padding: 1 2;
        border: tall #cfcfcf;
        background: #ffffff;
    }
    .message_title {
        text-style: bold;
        margin-bottom: 1;
    }
    .message_hint {
        color: #666666;
        margin-top: 1;
    }
    """
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self._title = title
        self._body = body

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._title, classes="message_title"),
            Static(self._body),
            Static("Press Esc to close", classes="message_hint"),
            classes="message",
        )

    def action_cancel(self) -> None:
        self.dismiss(None)


class EntryItem(ListItem):
    def __init__(self, entry: Entry, highlight_prefix: str = "") -> None:
        label = Label(format_entry(entry, highlight_prefix))
        super().__init__(label)
        self.entry = entry
        self.add_class("dir" if entry.is_dir else "file")


class BlobBrowser:
    def __init__(self, account: str, sas_token: str, container: str) -> None:
        container_url = f"https://{account}.blob.core.windows.net/{container}"
        if sas_token:
            container_url = f"{container_url}?{sas_token}"
        self._container = ContainerClient.from_container_url(container_url)

    def list_page(
        self,
        list_prefix: str,
        display_prefix: str,
        continuation_token: str | None,
    ) -> tuple[list[Entry], str | None]:
        pager = self._container.walk_blobs(
            name_starts_with=list_prefix,
            delimiter="/",
        ).by_page(continuation_token=continuation_token)
        page = next(pager, None)
        if page is None:
            return [], None

        entries: list[Entry] = []
        for item in page:
            name = item.name
            display = name[len(display_prefix) :] if name.startswith(display_prefix) else name
            if isinstance(item, BlobPrefix) or name.endswith("/"):
                entries.append(Entry(full_name=name, display=display, is_dir=True))
            else:
                entries.append(
                    Entry(
                        full_name=name,
                        display=display,
                        is_dir=False,
                        size=getattr(item, "size", None),
                    )
                )

        next_token = getattr(pager, "continuation_token", None)
        return sort_entries(entries), next_token

    def iter_blobs(self, prefix: str) -> Iterable:
        return self._container.list_blobs(name_starts_with=prefix)

    def download_blob(self, blob_name: str, dest_path: Path, progress_hook=None) -> None:
        blob_client = self._container.get_blob_client(blob_name)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("wb") as handle:
            stream = blob_client.download_blob(progress_hook=progress_hook)
            stream.readinto(handle)

    def upload_blob(self, local_path: Path, blob_name: str, progress_hook=None) -> None:
        blob_client = self._container.get_blob_client(blob_name)
        with local_path.open("rb") as handle:
            length = local_path.stat().st_size
            blob_client.upload_blob(
                handle,
                overwrite=True,
                length=length,
                progress_hook=progress_hook,
            )

    def delete_blob(self, blob_name: str) -> None:
        blob_client = self._container.get_blob_client(blob_name)
        blob_client.delete_blob(delete_snapshots="include")

    def get_blob_size(self, blob_name: str) -> int | None:
        try:
            props = self._container.get_blob_client(blob_name).get_blob_properties()
        except AzureError:
            return None
        return getattr(props, "size", None)


class BlobTUI(App):
    CSS = """
    Screen {
        background: #f2f2f2;
        color: #222222;
        padding: 0;
        layout: vertical;
    }
    #topbar {
        background: #f2f2f2;
        color: #222222;
        padding: 0 1;
        height: 1;
        align: center middle;
    }
    #main {
        border: tall #cfcfcf;
        background: #ffffff;
        padding: 0 2;
        margin: 0 1;
        height: 1fr;
    }
    #path {
        background: #ededed;
        color: #333333;
        padding: 0 1;
        border: round #d8d8d8;
        text-style: bold;
    }
    #status {
        background: #ededed;
        color: #444444;
        padding: 0 1;
        border: round #d8d8d8;
    }
    #help {
        background: #f2f2f2;
        color: #333333;
        padding: 0 1;
        height: 1;
        align: center middle;
    }
    #topbar_text, #help_text {
        text-align: center;
    }
    ListView {
        border: tall #d8d8d8;
        background: #ffffff;
        height: 1fr;
        scrollbar-size: 2 2;
        scrollbar-background: #ededed;
        scrollbar-background-hover: #e4e4e4;
        scrollbar-background-active: #d9d9d9;
        scrollbar-color: #b0b0b0;
        scrollbar-color-hover: #9a9a9a;
        scrollbar-color-active: #7f7f7f;
    }
    ListItem {
        padding: 0 1;
    }
    ListItem.-highlight {
        background: #e3e3e3;
    }
    ListItem.dir Label {
        color: #2b5d6c;
    }
    """

    BINDINGS = [
        ("right", "open", "Open"),
        ("left", "up", "Up"),
        ("pagedown", "next_page", "Next"),
        ("pageup", "prev_page", "Prev"),
        ("n", "next_page", "Next"),
        ("p", "prev_page", "Prev"),
        ("/", "filter_prefix", "Filter"),
        ("f", "filter_prefix", "PrefixFilter"),
        ("c", "clear_filter", "Clear"),
        ("g", "root", "Root"),
        ("d", "download", "Download"),
        ("u", "upload", "Upload"),
        ("x", "delete", "Delete"),
        ("i", "info", "Info"),
        ("r", "reload", "Reload"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        account: str,
        sas_token: str,
        container: str,
        base_prefix: str = "",
    ) -> None:
        super().__init__()
        self._account = account
        self._sas_token = sas_token
        self._container = container
        self._browser: BlobBrowser | None = None

        self._base_prefix = normalize_prefix(base_prefix)
        self._locked = LOCK_TO_DEFAULT_PREFIX and bool(self._base_prefix)
        self.prefix = self._base_prefix
        self.nav_stack: list[NavState] = []
        self.page_index = 0
        self.page_tokens: list[str | None] = [None]
        self.page_cache: dict[int, list[Entry]] = {}
        self.next_token: str | None = None
        self.prefix_filter = ""
        self.filter_stack: list[str] = []
        self.loading = False
        self.pending_entry: Entry | None = None
        self.pending_delete_entry: Entry | None = None
        self._filtered_entries: list[Entry] = []

    def compose(self) -> ComposeResult:
        yield Container(Static("Azure Blob Browser", id="topbar_text"), id="topbar")
        yield Container(
            Static(id="path"),
            ListView(id="list"),
            Static(id="status"),
            id="main",
        )
        yield Container(Static(id="help_text"), id="help")

    def on_mount(self) -> None:
        self._update_path()
        self.query_one("#list", ListView).focus()
        self._update_help()
        if not self._sas_token:
            self.push_screen(
                PromptScreen("SAS token", "e.g. sv=...&sig=..."),
                self._on_sas_result,
            )
        else:
            self._init_browser()
            self._load_page(reset=True)

    def _init_browser(self) -> None:
        if self._browser is None:
            self._browser = BlobBrowser(self._account, self._sas_token, self._container)

    def _on_sas_result(self, result: str | None) -> None:
        if result is None:
            self._set_status("SAS token required.")
            return
        sas = result.strip().lstrip("?")
        if not sas:
            self._set_status("SAS token required.")
            return
        self._sas_token = sas
        os.environ["AZURE_STORAGE_SAS_TOKEN"] = sas
        self._init_browser()
        self._load_page(reset=True)

    def _update_help(self) -> None:
        help_text = (
            "← Up  → Open  n/p Page  / Prefix  c Clear  g Root  d Download  "
            "u Upload  x Delete  q Quit"
        )
        self.query_one("#help_text", Static).update(help_text)

    def _update_path(self) -> None:
        path = f"{self._container}:/{self.prefix}"
        self.query_one("#path", Static).update(path)

    def _set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)

    def _selected_entry(self) -> Entry | None:
        list_view = self.query_one("#list", ListView)
        if list_view.index is None:
            return None
        if not self._filtered_entries:
            return None
        if list_view.index >= len(self._filtered_entries):
            return None
        return self._filtered_entries[list_view.index]

    def _refresh_list(self) -> None:
        entries = self.page_cache.get(self.page_index, [])
        self._filtered_entries = entries
        list_view = self.query_one("#list", ListView)
        list_view.clear()
        for entry in self._filtered_entries:
            list_view.append(EntryItem(entry, self.prefix_filter))
        if self._filtered_entries:
            list_view.index = 0
        summary = f"Page {self.page_index + 1} | Items {len(self._filtered_entries)}"
        if self.prefix_filter:
            summary += f" | Prefix '{self.prefix_filter}'"
        if self.loading:
            summary += " | Loading..."
        self._set_status(summary)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        detail = entry.display
        if not entry.is_dir and entry.size is not None:
            detail = f"{detail} ({format_size(entry.size)})"
        self._set_status(detail)

    def action_open(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        if entry.is_dir:
            if self.prefix_filter or self.filter_stack:
                self._push_nav_state(with_filters=False, needs_reload=True)
            else:
                self._push_nav_state()
            self.prefix = normalize_prefix(entry.full_name)
            self.page_index = 0
            self.page_tokens = [None]
            self.page_cache = {}
            self.prefix_filter = ""
            self.filter_stack = []
            self._update_path()
            self._load_page(reset=True)
        else:
            self._set_status("Use 'd' to download selected file.")

    def action_up(self) -> None:
        if not self.nav_stack:
            return
        state = self.nav_stack.pop()
        if self._locked and not state.prefix.startswith(self._base_prefix):
            self.nav_stack.append(state)
            self._set_status("Locked to base folder.")
            return
        if state.needs_reload:
            self.prefix = state.prefix
            self.page_index = 0
            self.page_tokens = [None]
            self.page_cache = {}
            self.prefix_filter = ""
            self.filter_stack = list(state.filter_stack)
            self._update_path()
            self._load_page(reset=True)
        else:
            self.prefix = state.prefix
            self.page_index = state.page_index
            self.page_tokens = state.page_tokens
            self.page_cache = state.page_cache
            self.prefix_filter = state.prefix_filter
            self.filter_stack = state.filter_stack
            self._update_path()
            self._refresh_list()

    def action_next_page(self) -> None:
        if self.loading:
            return
        if len(self.page_tokens) > self.page_index + 1:
            next_token = self.page_tokens[self.page_index + 1]
        else:
            next_token = self.next_token
        if not next_token:
            self._set_status("No more pages.")
            return
        self.page_index += 1
        if self.page_index in self.page_cache:
            self._refresh_list()
        else:
            self._load_page(continuation_token=next_token)

    def action_prev_page(self) -> None:
        if self.loading:
            return
        if self.page_index == 0:
            self._set_status("Already at first page.")
            return
        self.page_index -= 1
        if self.page_index in self.page_cache:
            self._refresh_list()
        else:
            token = self.page_tokens[self.page_index]
            self._load_page(continuation_token=token)

    def action_filter_prefix(self) -> None:
        self.push_screen(
            PromptScreen(
                "Filter (server-side, current directory)",
                "e.g. abc/ or abc/def",
            ),
            self._on_prefix_filter_result,
        )

    def _on_prefix_filter_result(self, result: str | None) -> None:
        if result is None:
            return
        raw = result.strip().lstrip("/")
        if not raw:
            return
        if self._locked:
            normalized = normalize_prefix(f"{self.prefix}{raw}")
            if not normalized.startswith(self._base_prefix):
                self._set_status("Locked to base folder.")
                return
        if "/" in raw:
            target_prefix, remaining = self._resolve_path(raw)
            if target_prefix != self.prefix:
                self._navigate_to_prefix(target_prefix)
            if remaining:
                self.filter_stack.append(self.prefix_filter)
                self.prefix_filter = remaining
                self._load_page(reset=True)
            return
        if self._dir_exists(raw):
            target = normalize_prefix(f"{self.prefix}{raw}")
            self._navigate_to_prefix(target)
            return
        self.filter_stack.append(self.prefix_filter)
        self.prefix_filter = raw
        self._load_page(reset=True)

    def action_clear_filter(self) -> None:
        if not self.prefix_filter:
            self._set_status("No filter to clear.")
            return
        if self.filter_stack:
            self.prefix_filter = self.filter_stack.pop()
        else:
            self.prefix_filter = ""
        self._load_page(reset=True)

    def action_root(self) -> None:
        if not self.nav_stack:
            self._set_status("Already at root.")
            return
        if self._locked:
            self.prefix = self._base_prefix
            self.nav_stack = []
            self.page_index = 0
            self.page_tokens = [None]
            self.page_cache = {}
            self.prefix_filter = ""
            self.filter_stack = []
            self._update_path()
            self._load_page(reset=True)
            return
        state = self.nav_stack[0]
        self.prefix = state.prefix
        self.nav_stack = []
        self.page_index = 0
        self.page_tokens = [None]
        self.page_cache = {}
        self.prefix_filter = ""
        self.filter_stack = []
        self._update_path()
        self._load_page(reset=True)

    def _push_nav_state(self, with_filters: bool = True, needs_reload: bool = False) -> None:
        prefix_filter = self.prefix_filter if with_filters else ""
        filter_stack = list(self.filter_stack) if with_filters else []
        self.nav_stack.append(
            NavState(
                prefix=self.prefix,
                page_index=self.page_index,
                page_tokens=list(self.page_tokens),
                page_cache=dict(self.page_cache),
                prefix_filter=prefix_filter,
                filter_stack=filter_stack,
                needs_reload=needs_reload,
            )
        )

    def _navigate_to_prefix(self, target_prefix: str) -> None:
        target_prefix = normalize_prefix(target_prefix)
        current_parts = [p for p in self.prefix.split("/") if p]
        target_parts = [p for p in target_prefix.split("/") if p]
        if target_parts[: len(current_parts)] == current_parts:
            remaining = target_parts[len(current_parts) :]
        else:
            remaining = target_parts

        if self.prefix_filter or self.filter_stack:
            self._push_nav_state(with_filters=False, needs_reload=True)
        else:
            self._push_nav_state()
        if remaining:
            path_parts: list[str] = []
            for segment in remaining[:-1]:
                path_parts.append(segment)
                prefix = normalize_prefix(f"{self.prefix}{'/'.join(path_parts)}")
                self.nav_stack.append(
                    NavState(
                        prefix=prefix,
                        page_index=0,
                        page_tokens=[None],
                        page_cache={},
                        prefix_filter="",
                        filter_stack=[],
                        needs_reload=True,
                    )
                )
        self.prefix = target_prefix
        self.page_index = 0
        self.page_tokens = [None]
        self.page_cache = {}
        self.prefix_filter = ""
        self.filter_stack = []
        self._update_path()
        self._load_page(reset=True)

    def _dir_exists(self, name: str) -> bool:
        prefix = normalize_prefix(f"{self.prefix}{name}")
        try:
            if self._browser is None:
                return False
            for _ in self._browser.iter_blobs(prefix):
                return True
        except AzureError:
            return False
        return False

    def _resolve_path(self, raw: str) -> tuple[str, str]:
        parts = [p for p in raw.split("/") if p]
        prefix = self.prefix
        remaining: list[str] = []
        for idx, part in enumerate(parts):
            if self._dir_exists(part):
                prefix = normalize_prefix(f"{prefix}{part}")
            else:
                remaining = parts[idx:]
                break
        return prefix, "/".join(remaining)

    def action_download(self) -> None:
        entry = self._selected_entry()
        if not entry:
            self._set_status("Select a file or directory first.")
            return
        self.pending_entry = entry
        self.push_screen(
            PromptScreen("Download to directory", "e.g. /tmp/downloads"),
            self._on_download_dir,
        )

    def _on_download_dir(self, result: str | None) -> None:
        entry = self.pending_entry
        self.pending_entry = None
        if entry is None or result is None or not result.strip():
            return
        dest_dir = Path(result).expanduser()
        self.run_worker(
            lambda: self._download_worker(entry, dest_dir),
            thread=True,
            group="transfer",
            exclusive=False,
        )

    def action_upload(self) -> None:
        self.push_screen(
            PromptScreen("Upload local path", "file or directory"),
            self._on_upload_path,
        )

    def _on_upload_path(self, result: str | None) -> None:
        if result is None or not result.strip():
            return
        local_path = Path(result).expanduser()
        self.run_worker(
            lambda: self._upload_worker(local_path),
            thread=True,
            group="transfer",
            exclusive=False,
        )

    def action_delete(self) -> None:
        entry = self._selected_entry()
        if not entry:
            self._set_status("Select a file or directory first.")
            return
        if self._locked and not entry.full_name.startswith(self._base_prefix):
            self._set_status("Locked to base folder.")
            return
        self.pending_delete_entry = entry
        label = entry.full_name if entry.full_name else entry.display
        if entry.is_dir and not label.endswith("/"):
            label = f"{label}/"
        title = f"Delete: {label}"
        hint = "Type DELETE to confirm"
        self.push_screen(
            PromptScreen(title, hint),
            self._on_delete_confirm_1,
        )

    def _on_delete_confirm_1(self, result: str | None) -> None:
        if result is None:
            self.pending_delete_entry = None
            return
        if result.strip().upper() != "DELETE":
            self._set_status("Delete canceled.")
            self.pending_delete_entry = None
            return
        entry = self.pending_delete_entry
        self.pending_delete_entry = None
        if entry is None:
            return
        self.run_worker(
            lambda: self._delete_worker(entry),
            thread=True,
            group="transfer",
            exclusive=False,
        )

    def action_info(self) -> None:
        entry = self._selected_entry()
        if not entry or entry.is_dir:
            self._set_status("Select a file to show its URL.")
            return
        url = f"https://{self._account}.blob.core.windows.net/{self._container}/{entry.full_name}"
        sas = self._sas_token
        if sas:
            url = f"{url}?{sas}"
        body = f"Blob: {entry.full_name}\nURL: {url}"
        self.push_screen(MessageScreen("Blob URL", body))

    def action_reload(self) -> None:
        if self.loading:
            return
        self._load_page(continuation_token=self.page_tokens[self.page_index])

    def _load_page(self, reset: bool = False, continuation_token: str | None = None) -> None:
        if reset:
            self.page_index = 0
            self.page_tokens = [None]
            self.page_cache = {}
            self.next_token = None
        self.loading = True
        self._refresh_list()
        self.run_worker(
            lambda: self._load_page_worker(continuation_token),
            thread=True,
            group="loading",
            exclusive=True,
        )

    def _load_page_worker(self, continuation_token: str | None) -> None:
        try:
            if self._browser is None:
                self.call_from_thread(self._set_status, "SAS token required.")
                self.call_from_thread(self._set_loading, False)
                return
            effective_prefix = f"{self.prefix}{self.prefix_filter}"
            entries, next_token = self._browser.list_page(
                effective_prefix, self.prefix, continuation_token
            )
            self.call_from_thread(self._apply_page, entries, next_token)
        except AzureError as exc:
            self.call_from_thread(self._set_status, f"Azure error: {exc}")
            self.call_from_thread(self._set_loading, False)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._set_status, f"Error: {exc}")
            self.call_from_thread(self._set_loading, False)

    def _set_loading(self, loading: bool) -> None:
        self.loading = loading
        self._refresh_list()

    def _apply_page(self, entries: list[Entry], next_token: str | None) -> None:
        self.page_cache[self.page_index] = entries
        self.next_token = next_token
        if len(self.page_tokens) <= self.page_index + 1:
            self.page_tokens.append(next_token)
        else:
            self.page_tokens[self.page_index + 1] = next_token
        self.loading = False
        self._refresh_list()

    def _make_progress_hook(self, label: str, total: int | None):
        last_update = 0.0
        total_bytes = total or 0

        def _hook(bytes_transferred: int, total_hint: int | None = None) -> None:
            nonlocal last_update
            nonlocal total_bytes
            if total_hint:
                total_bytes = total_hint
            now = time.monotonic()
            if now - last_update < 0.25 and bytes_transferred != total_bytes:
                return
            last_update = now
            if total_bytes:
                percent = bytes_transferred / total_bytes * 100
                message = (
                    f"{label} {format_size(bytes_transferred)}/"
                    f"{format_size(total_bytes)} ({percent:.1f}%)"
                )
            else:
                message = f"{label} {format_size(bytes_transferred)}"
            self.call_from_thread(self._set_status, message)

        return _hook

    def _make_aggregate_progress_hook(self, label: str, total: int | None):
        last_update = 0.0
        total_bytes = total or 0
        overall_done = 0
        per_file_prev: dict[str, int] = {}

        def _for_file(file_key: str):
            def _hook(bytes_transferred: int, total_hint: int | None = None) -> None:
                nonlocal last_update
                nonlocal total_bytes
                nonlocal overall_done
                prev = per_file_prev.get(file_key, 0)
                if bytes_transferred < prev:
                    prev = 0
                delta = bytes_transferred - prev
                per_file_prev[file_key] = bytes_transferred
                overall_done += delta
                now = time.monotonic()
                if now - last_update < 0.25 and overall_done != total_bytes:
                    return
                last_update = now
                if total_bytes:
                    percent = min(overall_done / total_bytes * 100, 100.0)
                    message = (
                        f"{label} {format_size(overall_done)}/"
                        f"{format_size(total_bytes)} ({percent:.1f}%)"
                    )
                else:
                    message = f"{label} {format_size(overall_done)}"
                self.call_from_thread(self._set_status, message)

            return _hook

        return _for_file

    def _download_worker(self, entry: Entry, dest_dir: Path) -> None:
        try:
            if self._browser is None:
                self.call_from_thread(self._set_status, "SAS token required.")
                return
            if entry.is_dir:
                base = dest_dir / Path(entry.display).name
                self.call_from_thread(self._set_status, "Scanning folder...")
                blobs = list(self._browser.iter_blobs(entry.full_name))
                total_bytes = sum(getattr(blob, "size", 0) or 0 for blob in blobs)
                progress_for = self._make_aggregate_progress_hook(
                    f"Downloading {entry.display.rstrip('/')}/", total_bytes
                )
                failed = 0
                last_error: str | None = None
                for blob in blobs:
                    rel = blob.name[len(entry.full_name) :]
                    if not rel:
                        continue
                    progress = progress_for(rel)
                    try:
                        self._browser.download_blob(blob.name, base / rel, progress)
                    except AzureError as exc:
                        failed += 1
                        last_error = str(exc)
                    except Exception as exc:  # noqa: BLE001
                        failed += 1
                        last_error = str(exc)
                if failed:
                    message = f"Download complete with {failed} failed."
                    if last_error:
                        message = f"{message} Last error: {last_error}"
                    self.call_from_thread(self._set_status, message)
                else:
                    self.call_from_thread(self._set_status, "Download complete.")
            else:
                dest = dest_dir / Path(entry.display).name
                total = self._browser.get_blob_size(entry.full_name)
                progress = self._make_progress_hook(f"Downloading {entry.display}...", total)
                try:
                    self._browser.download_blob(entry.full_name, dest, progress)
                    self.call_from_thread(self._set_status, "Download complete.")
                except AzureError as exc:
                    self.call_from_thread(self._set_status, f"Download failed: {exc}")
                except Exception as exc:  # noqa: BLE001
                    self.call_from_thread(self._set_status, f"Download failed: {exc}")
        except AzureError as exc:
            self.call_from_thread(self._set_status, f"Azure error: {exc}")
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._set_status, f"Error: {exc}")

    def _upload_worker(self, local_path: Path) -> None:
        try:
            if self._browser is None:
                self.call_from_thread(self._set_status, "SAS token required.")
                return
            if not local_path.exists():
                self.call_from_thread(self._set_status, "Local path not found.")
                return
            if local_path.is_file():
                blob_name = f"{self.prefix}{local_path.name}"
                total = local_path.stat().st_size
                progress = self._make_progress_hook(f"Uploading {local_path.name}...", total)
                try:
                    self._browser.upload_blob(local_path, blob_name, progress)
                    self.call_from_thread(self._set_status, "Upload complete.")
                except AzureError as exc:
                    self.call_from_thread(self._set_status, f"Upload failed: {exc}")
                except Exception as exc:  # noqa: BLE001
                    self.call_from_thread(self._set_status, f"Upload failed: {exc}")
            else:
                base_prefix = f"{self.prefix}{local_path.name}/"
                self.call_from_thread(self._set_status, "Scanning folder...")
                files: list[Path] = []
                total_bytes = 0
                for root, _, filenames in os.walk(local_path):
                    for filename in filenames:
                        src = Path(root) / filename
                        files.append(src)
                        total_bytes += src.stat().st_size
                progress_for = self._make_aggregate_progress_hook(
                    f"Uploading {local_path.name}/", total_bytes
                )
                failed = 0
                last_error: str | None = None
                for src in files:
                    rel = src.relative_to(local_path)
                    blob_name = f"{base_prefix}{rel.as_posix()}"
                    progress = progress_for(rel.as_posix())
                    try:
                        self._browser.upload_blob(src, blob_name, progress)
                    except AzureError as exc:
                        failed += 1
                        last_error = str(exc)
                    except Exception as exc:  # noqa: BLE001
                        failed += 1
                        last_error = str(exc)
                if failed:
                    message = f"Upload complete with {failed} failed."
                    if last_error:
                        message = f"{message} Last error: {last_error}"
                    self.call_from_thread(self._set_status, message)
                else:
                    self.call_from_thread(self._set_status, "Upload complete.")
                self.call_from_thread(self.action_reload)
        except AzureError as exc:
            self.call_from_thread(self._set_status, f"Azure error: {exc}")
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._set_status, f"Error: {exc}")

    def _delete_worker(self, entry: Entry) -> None:
        try:
            if self._locked and not entry.full_name.startswith(self._base_prefix):
                self.call_from_thread(self._set_status, "Locked to base folder.")
                return
            if entry.is_dir:
                prefix = normalize_prefix(entry.full_name)
                if self._locked and not prefix.startswith(self._base_prefix):
                    self.call_from_thread(self._set_status, "Locked to base folder.")
                    return
                deleted = 0
                for blob in self._browser.iter_blobs(prefix) if self._browser else []:
                    if self._browser:
                        self._browser.delete_blob(blob.name)
                    deleted += 1
                    if deleted % 50 == 0:
                        self.call_from_thread(self._set_status, f"Deleted {deleted} blobs...")
                self.call_from_thread(
                    self._set_status,
                    f"Delete complete. {deleted} blobs removed.",
                )
            else:
                if self._browser:
                    self._browser.delete_blob(entry.full_name)
                self.call_from_thread(self._set_status, "Delete complete.")
            self.call_from_thread(self.action_reload)
        except AzureError as exc:
            self.call_from_thread(self._set_status, f"Azure error: {exc}")
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._set_status, f"Error: {exc}")


@dataclass(frozen=True)
class NavState:
    prefix: str
    page_index: int
    page_tokens: list[str | None]
    page_cache: dict[int, list[Entry]]
    prefix_filter: str
    filter_stack: list[str]
    needs_reload: bool = False


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    units = ["KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        value /= 1024.0
        if value < 1024:
            return f"{value:.1f} {unit}"
    return f"{value:.1f} PB"


def _highlight_prefix(text: str, prefix: str) -> Text:
    rich_text = Text(text)
    if prefix and text.startswith(prefix):
        rich_text.stylize("bold", 0, len(prefix))
    return rich_text


def format_entry(entry: Entry, highlight_prefix: str = "") -> Text:
    if entry.is_dir:
        display = f"{entry.display.rstrip('/')}/"
        return _highlight_prefix(display, highlight_prefix)
    size_text = format_size(entry.size) if entry.size is not None else "?"
    return Text(f"{size_text:>8}  ") + _highlight_prefix(entry.display, highlight_prefix)


def sort_entries(entries: list[Entry]) -> list[Entry]:
    dirs = sorted(
        (entry for entry in entries if entry.is_dir),
        key=lambda item: item.display.lower(),
    )
    files = sorted(
        (entry for entry in entries if not entry.is_dir),
        key=lambda item: item.display.lower(),
    )
    return dirs + files


def main() -> None:
    parser = argparse.ArgumentParser(description="Azure Blob TUI")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Configure account/container/prefix and overwrite the local config file",
    )
    args = parser.parse_args()
    settings = load_settings(args.configure, interactive=True)
    account, sas = ensure_env(settings.get("account_name", ACCOUNT_NAME))
    app = BlobTUI(
        account=account,
        sas_token=sas,
        container=settings.get("container_name", CONTAINER_NAME),
        base_prefix=settings.get("default_prefix", DEFAULT_PREFIX),
    )
    app.run()


if __name__ == "__main__":
    main()
