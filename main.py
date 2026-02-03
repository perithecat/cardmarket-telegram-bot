import os
import requests
import sys

def telegram_send(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()

def ct_get(path, params=None):
    jwt = os.environ["CARDTRADER_JWT"].strip()
    headers = {"Authorization": "Bearer " + jwt}
    url = "https://api.cardtrader.com" + path
    return requests.get(url, headers=headers, params=params, timeout=30)

def main():
    # JWT check
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT caducado</b>. Actualiza <b>CARDTRADER_JWT</b>.")
        sys.exit(1)
    r.raise_for_status()

    # Buscar blueprints por nombre (MTG = 1, Single Cards = 1)
    params = {"game_id": 1, "category_id": 1, "name": "The One Ring", "per_page": 50}
    r = ct_get("/api/v2/blueprints", params=params)
    r.raise_for_status()
    items = r.json()

    if not isinstance(items, list) or not items:
        telegram_send("⚠️ No encontré resultados para The One Ring.")
        return

    lines = []
    lines.append("<b>🧾 The One Ring — blueprints encontrados</b>")
    lines.append("(elige cuál usar para precios)")
    lines.append("")

    for i, b in enumerate(items, 1):
        bid = str(b.get("id", ""))
        name = str(b.get("name", ""))
        exp = str(b.get("expansion_id", ""))
        slug = str(b.get("slug", ""))
        meta = str(b.get("meta_name", ""))
        lines.append(f"{i}) id=<code>{bid}</code> exp=<code>{exp}</code>")
        lines.append(f"   <b>{name}</b>")
        lines.append(f"   meta=<code>{meta}</code>")
        lines.append(f"   slug=<code>{slug}</code>")
        lines.append("")

    msg = "\n".join(lines)
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...\n<i>(recortado)</i>"
    telegram_send(msg)

if __name__ == "__main__":
    main()
