import os
import requests
import sys


def telegram_send(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def cardtrader_get(path):
    jwt = os.environ["CARDTRADER_JWT"].strip()
    headers = {"Authorization": "Bearer " + jwt}
    url = "https://api.cardtrader.com" + path
    return requests.get(url, headers=headers, timeout=30)


def main():
    # 1) Check JWT
    r = cardtrader_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>JWT caducado o sin permisos</b>\n"
            "Entra en CardTrader → Token JWT → copia uno nuevo\n"
            "y actualiza el secreto <b>CARDTRADER_JWT</b> en GitHub."
        )
        sys.exit(1)
    r.raise_for_status()

    # 2) Games
    r = cardtrader_get("/api/v2/games")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>Sin permisos</b> para /games (401/403).")
        sys.exit(1)
    r.raise_for_status()

    games = r.json()

    # 3) Detect magic
    magic_found = None
    if isinstance(games, list):
        for g in games:
            if isinstance(g, str) and ("magic" in g.lower()):
                magic_found = g
                break
            if isinstance(g, dict):
                name = str(g.get("name", "")).lower()
                slug = str(g.get("slug", "")).lower()
                if ("magic" in name) or ("magic" in slug):
                    magic_found = g
                    break

    snippet = str(games)[:900]

    if magic_found is None:
        msg = "✅ <b>Conexión OK</b>\nNo encuentro 'Magic' en /games.\n\n<code>" + snippet + "</code>"
        telegram_send(msg)
        return

    if isinstance(magic_found, dict):
        name = str(magic_found.get("name", "Magic"))
        mid = str(magic_found.get("id", ""))
        slug = str(magic_found.get("slug", ""))
        msg = (
            "✅ <b>CardTrader API OK</b>\n\n"
            "Juego detectado: <b>" + name + "</b>\n"
            "id: <code>" + mid + "</code>\n"
            "slug: <code>" + slug + "</code>\n\n"
            "<code>" + snippet + "</code>"
        )
        telegram_send(msg)
    else:
        msg = (
            "✅ <b>CardTrader API OK</b>\n\n"
            "Juego detectado: <b>" + str(magic_found) + "</b>\n\n"
            "<code>" + snippet + "</code>"
        )
        telegram_send(msg)


if __name__ == "__main__":
    main()
