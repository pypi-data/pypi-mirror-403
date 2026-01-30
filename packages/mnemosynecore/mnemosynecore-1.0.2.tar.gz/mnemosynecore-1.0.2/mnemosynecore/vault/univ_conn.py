import json
from typing import Dict, Union
from mattermostdriver import Driver
from sqlalchemy import create_engine
from mnemosynecore.vault.client import get_connection_as_json


def un_conn(conn_id: str, conn_type: str) -> Union[Driver, "Engine", Dict, object]:
    cfg = json.loads(get_connection_as_json(conn_id))
    conn_type = conn_type.lower()

    if conn_type == "vertica":
        vertica_url = (
            f"vertica+vertica_python://{cfg['login']}:{cfg['password']}@"
            f"{cfg['host']}:{cfg['port']}/{cfg.get('schema')}"
        )
        return create_engine(vertica_url, pool_pre_ping=True)

    elif conn_type == "clickhouse":
        from clickhouse_driver import Client

        return Client(
            host=cfg["host"],
            port=int(cfg.get("port", 9000)),
            user=cfg.get("login"),
            password=cfg.get("password"),
            database=cfg.get("schema") or cfg.get("database"),
            secure=cfg.get("secure", False),
        )

    elif conn_type == "superset":
        return {
            "host": cfg["host"],
            "login": cfg.get("login"),
            "password": cfg.get("password"),
            "schema": cfg.get("schema", "https"),
            "port": int(cfg.get("port", 443)),
            "extra": json.loads(cfg.get("extra", "{}")),
        }

    elif conn_type == "mattermost":
        driver = Driver({
            "url": cfg["host"],
            "token": cfg["password"],
            "scheme": cfg.get("schema", "https"),
            "port": int(cfg.get("port", 443)),
            "basepath": json.loads(cfg.get("extra", "{}")).get("basepath", "/api/v4"),
        })
        driver.login()
        return driver

    elif conn_type == "raw":
        return cfg

    else:
        raise ValueError(f"Неизвестный conn_type: {conn_type}")