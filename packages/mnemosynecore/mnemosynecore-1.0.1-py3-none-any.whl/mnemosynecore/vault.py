import json
import os
from typing import Dict, Optional


def get_connection_as_json(conn_id: str) -> str:
    secret = os.environ.get(conn_id)

    if not secret:
        try:
            from mnemosynecore.vault.client import VaultClient
            vault_client = VaultClient()

            secret = vault_client.get_secret(conn_id)

            if not secret:
                raise ValueError(f"Секрет {conn_id} не найден ни в переменных окружения, ни в Vault")

        except ImportError:
            raise ValueError(f"Секрет {conn_id} не найден в переменных окружения и не удалось подключиться к Vault")
        except Exception as e:
            raise ValueError(f"Ошибка при получении секрета {conn_id} из Vault: {str(e)}")

    return secret


def get_secret(conn_id: str) -> Dict:
    raw = get_connection_as_json(conn_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Секрет {conn_id} не является корректным JSON: {e}")


def get_connection_as_json_test(
    conn_id: str,
    dir_path: str | None = None,
) -> str:

    filename = f"{conn_id}.json"
    search_paths: list[str] = []

    if dir_path:
        search_paths.append(os.path.abspath(dir_path))

    search_paths.append(os.getcwd())

    for base in search_paths:
        file_path = os.path.join(base, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

    raise FileNotFoundError(
        f"Тестовый секрет {filename} не найден. "
        f"Проверены пути: {search_paths}"
    )


def get_secret_test(conn_id: str, dir_path: str | None = None) -> Dict:
    raw = get_connection_as_json_test(conn_id, dir_path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Тестовый секрет {conn_id} не является корректным JSON: {e}"
        )