import requests
from .vault import get_secret
from superset_o3_api_lib import SupersetAPIClient
import json
import os
from typing import List, Dict, Optional


def superset_request(
    *,
    endpoint: str,
    method: str = "GET",
    payload: dict | None = None,
    vault_conn_id: str
):

    cfg = get_secret(vault_conn_id)
    base_url = cfg["host"]

    headers = {
        "Authorization": f"Bearer {cfg['password']}",
        "Content-Type": "application/json",
    }

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    resp = requests.request(method, url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def superset_screenshot_dashboard(
    conn_id: str,
    dashboards: List[Dict],
    dir_path: Optional[str] = None,
    output_dir: str = ".",
) -> List[str]:

    from superset_o3_api_lib import SupersetAPIClient
    from superset_o3_api_lib.auth import PasswordOAuthFlow
    from mnemosynecore.secrets import resolve_secret
    import os

    cfg = resolve_secret(conn_id, dir_path)

    extra = cfg.get("extra") or {}
    if isinstance(extra, str):
        extra = json.loads(extra)

    client_secret = extra.get("client_secret")

    auth = PasswordOAuthFlow(
        superset_host=cfg["host"],
        username=cfg["login"],
        password=cfg["password"],
        client_id=cfg["schema"],
        client_secret=client_secret,
    )

    api_client = SupersetAPIClient(auth=auth)

    saved_files: List[str] = []

    for i, dashboard in enumerate(dashboards, start=1):
        screenshot = api_client.dashboard_screenshot(
            dashboard_id=dashboard.get("id"),
            dashboard_url=dashboard.get("url"),
            refresh=True,
            refresh_wait_sec=40,
            thumb_size=(2048, 1036),
            window_size=(2048, 1036),
            retry_count=5,
        )

        name = dashboard.get("id") or "url"
        filename = os.path.join(output_dir, f"{i}_{name}.png")

        with open(filename, "wb") as f:
            f.write(screenshot)

        saved_files.append(filename)

    return saved_files