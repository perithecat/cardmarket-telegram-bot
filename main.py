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

def cardtrader_get(path: str):
    jwt = os.environ["CARDTRADER_JWT"].strip()
    headers = {"Authorization": f"Bearer {jwt}"}
    url = f"https://api.cardtrader.com{path}"
    r = requests.get(url, headers=headers, timeout=30)
    return r

def main():
    # 1) Health check (para saber si el JWT sirve)
    r = cardtrader_get("/api/v2/info")

    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>CardTrader JWT caducado o sin permisos</b>\n\n"
            "El bot no puede renovar el token automáticamente.\n"
            "Solución: entra en CardTrader → Token JWT → copia uno nuevo y "
            "actualiza el secreto <b>CARDTRADER_JWT</b> en GitHub.\n\n"
            f"Error: {r.status_code}"
        )
        # Salimos con error para que quede claro en Actions
        sys.exit(1)

    r.raise_for_status()

    # 2) Si llega aquí, el JWT está OK
    telegram_send("✅ CardTrader JWT OK. Bot activo y listo para pedir datos.")
    # Aquí ya enganchamos el siguiente paso: buscar cartas/listings y mandar ranking.

if __name__ == "__main__":
    main()
