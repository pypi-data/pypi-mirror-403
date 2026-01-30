from typing import Dict, Optional
from mnemosynecore.vault.client import get_secret, get_secret_test


def resolve_secret(
    conn_id: str,
    dir_path: Optional[str] = None,
) -> Dict:
    try:
        return get_secret_test(conn_id, dir_path)
    except FileNotFoundError:
        return get_secret(conn_id)