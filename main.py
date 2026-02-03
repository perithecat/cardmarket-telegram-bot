import os
import requests
import sys

def telegram_send(text: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()

def cardtrader_get(path: str, params=None):
    jwt = os.environ["CARDTRADER_JWT"].strip()
    headers = {"Authorization": f"Bearer {jwt}"}
    url = f"https://api.cardtrader.com{path}"
    r = requests.get(url, headers=headers, params=params, timeout=30)
    return r

def main():
    # 1) Check JWT
    r = cardtrader_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>JWT caducado</b>\n"
            "Copia uno nuevo en CardTrader y actualiza el secreto <b>CARDTRADER_JWT</b>."
        )
        sys.exit(1)
    r.raise_for_status()

    # 2) Traer lista de juegos
    r = cardtrader_get("/api/v2/games")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT sin permisos</b> para /games (401/403).")
        sys.exit(1)
    r.raise_for_status()

games = r.json()

magic = None
for g in games:
    if isinstance(g, str) and "magic" in g.lower():
        magic = g
        break

    if not magic:
    telegram_send("✅ Conexión OK, pero no encontré 'Magic' en /games.")
    return

msg = (
    "<b>✅ CardTrader API OK</b>\n\n"
    f"Juego detectado: <b>{magic}</b>"
)
telegram_send(msg)


if __name__ == "__main__":
    main()
