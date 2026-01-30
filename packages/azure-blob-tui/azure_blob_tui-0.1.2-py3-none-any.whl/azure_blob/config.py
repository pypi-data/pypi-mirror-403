from __future__ import annotations

import os
from getpass import getpass
from pathlib import Path
from urllib.parse import urlparse

from platformdirs import user_config_path

ACCOUNT_NAME = ""
DEFAULT_PREFIX = ""
LOCK_TO_DEFAULT_PREFIX = True
CONTAINER_NAME = ""

APP_NAME = "azure-blob-tui"
APP_AUTHOR = "leo1oel"
CONFIG_ENV = "AZURE_BLOB_TUI_CONFIG"
CONFIG_SECTION = "azure_blob_tui"
CONFIG_KEYS = ("account_name", "container_name", "default_prefix")
SAS_PASSPHRASE_ENV = "AZURE_BLOB_TUI_PASSPHRASE"
SAS_FILENAME = "sas.enc"


def normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    return prefix if prefix.endswith("/") else f"{prefix}/"


def config_path() -> Path:
    env_path = os.environ.get(CONFIG_ENV, "").strip()
    if env_path:
        return Path(env_path).expanduser()
    return user_config_path(APP_NAME, APP_AUTHOR) / "config.toml"


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def read_config() -> dict[str, str]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    section = data.get(CONFIG_SECTION, {})
    return {
        key: str(section.get(key, "")).strip()
        for key in CONFIG_KEYS
        if section.get(key, "") is not None
    }


def write_config(values: dict[str, str]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"[{CONFIG_SECTION}]"]
    for key in CONFIG_KEYS:
        value = values.get(key, "").strip()
        lines.append(f'{key} = "{_toml_escape(value)}"')
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _prompt_value(label: str, default: str) -> str:
    if default:
        prompt = f"{label} [{default}]: "
    else:
        prompt = f"{label}: "
    value = input(prompt).strip()
    return value or default


def _configure_values(existing: dict[str, str]) -> dict[str, str]:
    account = _prompt_value("Azure Storage account", existing.get("account_name", ""))
    container = _prompt_value("Container name", existing.get("container_name", ""))
    prefix = _prompt_value("Default prefix (optional)", existing.get("default_prefix", ""))
    return {
        "account_name": account,
        "container_name": container,
        "default_prefix": normalize_prefix(prefix),
    }


def _prompt_yes_no(label: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    choice = input(f"{label} {suffix}: ").strip().lower()
    if not choice:
        return default
    return choice in {"y", "yes"}


def _sas_path() -> Path:
    return config_path().parent / SAS_FILENAME


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    from base64 import urlsafe_b64encode

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def _encrypt_sas(token: str, passphrase: str) -> str:
    from base64 import urlsafe_b64encode
    from os import urandom

    from cryptography.fernet import Fernet

    salt = urandom(16)
    key = _derive_key(passphrase, salt)
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(token.encode("utf-8"))
    return f"v1:{urlsafe_b64encode(salt).decode('ascii')}:{ciphertext.decode('ascii')}"


def _decrypt_sas(payload: str, passphrase: str) -> str:
    from base64 import urlsafe_b64decode

    from cryptography.fernet import Fernet, InvalidToken

    version, salt_b64, cipher = payload.split(":", 2)
    if version != "v1":
        return ""
    salt = urlsafe_b64decode(salt_b64.encode("ascii"))
    key = _derive_key(passphrase, salt)
    fernet = Fernet(key)
    try:
        return fernet.decrypt(cipher.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ""


def _get_passphrase(prompt: bool) -> str:
    env_value = os.environ.get(SAS_PASSPHRASE_ENV, "").strip()
    if env_value:
        return env_value
    if not prompt:
        return ""
    return getpass("SAS passphrase (will be used to encrypt/decrypt): ").strip()


def get_sas_token(prompt: bool = False) -> str:
    env_token = os.environ.get("AZURE_STORAGE_SAS_TOKEN", "").strip()
    if env_token:
        return env_token
    path = _sas_path()
    if not path.exists():
        return ""
    passphrase = _get_passphrase(prompt=prompt)
    if not passphrase:
        return ""
    try:
        payload = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return _decrypt_sas(payload, passphrase).strip()


def normalize_sas_token(sas: str) -> tuple[str, str | None]:
    sas = sas.strip()
    if not sas:
        return "", None
    account_from_url: str | None = None
    if "blob.core.windows.net" in sas and "?" in sas:
        parsed = urlparse(sas)
        if parsed.netloc.endswith(".blob.core.windows.net"):
            account_from_url = parsed.netloc.split(".blob.core.windows.net")[0]
        sas = parsed.query
    if sas.startswith("?"):
        sas = sas[1:]
    return sas, account_from_url


def set_sas_token(token: str) -> None:
    passphrase = _get_passphrase(prompt=True)
    if not passphrase:
        raise RuntimeError("Missing passphrase for SAS encryption.")
    payload = _encrypt_sas(token, passphrase)
    path = _sas_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def clear_sas_token() -> None:
    path = _sas_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            return


def load_settings(force_configure: bool = False, interactive: bool = False) -> dict[str, str]:
    settings = read_config()
    missing = any(not settings.get(key, "").strip() for key in CONFIG_KEYS[:2])
    if force_configure or (interactive and missing):
        settings = _configure_values(settings)
        write_config(settings)
    if force_configure:
        existing = get_sas_token() or os.environ.get("AZURE_STORAGE_SAS_TOKEN", "").strip()
        if not existing and _prompt_yes_no(
            "Store SAS token in encrypted local file?", default=False
        ):
            sas = _prompt_value("Azure Storage SAS token", "")
            if sas:
                set_sas_token(sas)
    env_account = os.environ.get("AZURE_STORAGE_ACCOUNT", "").strip()
    env_container = os.environ.get("AZURE_BLOB_TUI_CONTAINER", "").strip()
    env_prefix = os.environ.get("AZURE_BLOB_TUI_PREFIX", "").strip()
    if env_account:
        settings["account_name"] = env_account
    if env_container:
        settings["container_name"] = env_container
    if env_prefix:
        settings["default_prefix"] = normalize_prefix(env_prefix)
    return settings


def ensure_env(account_fallback: str) -> tuple[str, str]:
    account = account_fallback or os.environ.get("AZURE_STORAGE_ACCOUNT", "").strip()
    sas = get_sas_token(prompt=True)

    if not account:
        account = input("Azure Storage account: ").strip()

    sas, account_from_url = normalize_sas_token(sas)
    if account_from_url:
        account = account_from_url

    os.environ["AZURE_STORAGE_ACCOUNT"] = account
    if sas:
        os.environ["AZURE_STORAGE_SAS_TOKEN"] = sas
    return account, sas
