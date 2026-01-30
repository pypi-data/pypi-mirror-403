import json
import os
from typing import Dict, Optional


class VaultClient:
    def __init__(self):
        pass

    def get_secret(self, conn_id: str) -> Optional[str]:
        return None


def get_connection_as_json(conn_id: str) -> str:
    secret = os.environ.get(conn_id)
    if secret:
        return secret

    try:
        vault_client = VaultClient()
        secret = vault_client.get_secret(conn_id)
        if secret:
            return secret
    except Exception as e:
        pass

    try:
        from airflow.hooks.base_hook import BaseHook
        conn = BaseHook.get_connection(conn_id)
        ci = {
            "host": conn.host,
            "password": conn.password,
            "login": conn.login,
            "port": conn.port,
            "schema": conn.schema,
            "extra": conn.extra
        }
        return json.dumps(ci)
    except ImportError:
        pass
    except Exception as e:
        pass

    raise ValueError(
        f"Секрет {conn_id} не найден в переменных окружения, Vault или Airflow"
    )


def get_secret(conn_id: str) -> Dict:
    raw = get_connection_as_json(conn_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Секрет {conn_id} не является корректным JSON: {e}")


def get_connection_as_json_test(conn_id: str, dir_path: Optional[str] = None) -> str:
    filename = f"{conn_id}.json"
    search_paths = []
    if dir_path:
        search_paths.append(os.path.abspath(dir_path))
    search_paths.append(os.getcwd())

    for base in search_paths:
        file_path = os.path.join(base, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

    raise FileNotFoundError(
        f"Тестовый секрет {filename} не найден. Проверены пути: {search_paths}"
    )


def get_secret_test(conn_id: str, dir_path: Optional[str] = None) -> Dict:
    raw = get_connection_as_json_test(conn_id, dir_path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Тестовый секрет {conn_id} не является корректным JSON: {e}")