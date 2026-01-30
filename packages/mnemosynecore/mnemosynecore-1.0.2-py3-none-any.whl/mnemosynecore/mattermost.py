import logging
from mattermostdriver import Driver
from mnemosynecore.vault.univ_conn import un_conn


def get_mattermost_driver(bot_id: str) -> Driver:
    if bot_id.startswith('{'):
        import json
        try:
            cfg = json.loads(bot_id)
        except json.JSONDecodeError:
            raise ValueError("Неверный формат JSON для конфигурации Mattermost")

        driver = Driver({
            "url": cfg["host"],
            "token": cfg["password"],
            "scheme": cfg.get("schema", "https"),
            "port": int(cfg.get("port", 443)),
            "basepath": cfg.get("basepath", "/api/v4"),
        })
        driver.login()
        return driver

    return un_conn(bot_id, "mattermost")


def send_message(
    *,
    channel_id: str,
    bot_id: str,
    text: str,
    silent: bool = False,
) -> None:
    driver = get_mattermost_driver(bot_id)

    try:
        driver.posts.create_post(
            options={"channel_id": channel_id, "message": text.strip()}
        )
        if not silent:
            logging.info("Сообщение отправлено в Mattermost: %s", channel_id)
    except Exception as exc:
        logging.exception(
            "Ошибка отправки сообщения в Mattermost (channel_id=%s)", channel_id
        )
        raise


def send_message_test(
    *,
    channel_id: str,
    bot_id: str,
    text: str,
    dir_path: str | None = None,
    silent: bool = False,
) -> None:
    from mnemosynecore.vault.client import get_secret_test

    cfg = get_secret_test(bot_id, dir_path)
    driver = Driver({
        "url": cfg["host"],
        "token": cfg["password"],
        "scheme": cfg.get("schema", "https"),
        "port": int(cfg.get("port", 443)),
        "basepath": cfg.get("basepath", "/api/v4"),
    })
    driver.login()

    try:
        driver.posts.create_post(
            options={"channel_id": channel_id, "message": text.strip()}
        )
        if not silent:
            print(f"[TEST] Сообщение отправлено в Mattermost: {channel_id}")
    except Exception as exc:
        print(f"[TEST] Ошибка отправки сообщения: {exc}")
        raise