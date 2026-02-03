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


def detect_magic(games_json):
    """
    Intenta encontrar Magic en la respuesta de /games,
    sea lista de strings o lista de dicts.
    """
    if isinstance(games_json, list):
        for g in games_json:
            # Caso 1: lista de strings
            if isinstance(g, str) and "magic" in g.lower():
                return g

            # Caso 2: lista de dicts
            if isinstance(g, dict):
                name = str(g.get("name", "")).lower()
                slug = str(g.get("slug", "")).lower()
                if "magic" in name or "magic" in slug:
                    return g

    # Si no encaja con nada
    return None


def main():
    # 1) Health check JWT
    r = cardtrader_get("/api/v2/info")

    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>CardTrader JWT caducado o sin permisos</b>\n\n"
            "Solución:\n"
            "1) CardTrader → Token JWT → copiar token nuevo\n"
            "2) GitHub → Settings → Secrets → actualizar <b>CARDTRADER_JWT</b>\n\n"
            f"HTTP: {r.status_code}"
        )
        sys.exit(1)

    try:
        r.raise_for_status()
    except Exception:
        telegram_send(
            "⚠️ <b>Error llamando a /info</b>\n\n"
            f"HTTP: {r.status_code}\n"
            f"Respuesta: <code>{(r.text or '')[:300]}</code>"
        )
        sys.exit(1)

    # 2) Pedir /games
    r = cardtrader_get("/api/v2/games")

    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>JWT sin permisos para /games</b>\n\n"
            f"HTTP: {r.status_code}\n"
            "Copia un JWT nuevo y actualiza <b>CARDTRADER_JWT</b>."
        )
        sys.exit(1)

    try:
        r.raise_for_status()
    except Exception:
        telegram_send(
            "⚠️ <b>Error llamando a /games</b>\n\n"
            f"HTTP: {r.status_code}\n"
            f"Respuesta: <code>{(r.text or '')[:300]}</code>"
        )
        sys.exit(1)

    games = r.json()

    # 3) Detectar Magic si se puede
    magic = detect_magic(games)

    # 4) Mandar a Telegram un resumen (y parte del payload para debug)
    snippet = str(games)[:900]  # recorte para no pasarnos de tamaño

    if magic is None:
        telegram_send(
            "✅ <b>Conexión OK</b>\n"
            "Pero no encontré 'Magic' en /games.\n\n"
            "<b>Primeros datos (recorte):</b>\n"
            f"<code>{snippet}</code>"
        )
        return

    # Si magic es dict, formatea; si es string, lo manda tal cual
    if isinstance(magic, dict):
        name = magic.get("name", "Magic")
        mid = magic.get("id", "¿?")
        slug = magic.get("slug", "")
        telegram_send(
            "✅ <b>CardTrader API OK</b>\n\n"
            f"Juego detectado: <b>{name}</b>\n"
            f"id: <code>{mid}</code>\n"
            f"slug: <code>{slug}</code>\n\n"
            "<b>Recorte /games:</b>\n"
            f"<code>{snippet}</code>"
        )
    else:
        telegram_send(
            "✅ <b>CardTrader API OK</b>\n\n"
            f"Juego detectad
