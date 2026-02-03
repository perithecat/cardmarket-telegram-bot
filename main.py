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

def pick_names(items, limit=5):
    out = []
    if isinstance(items, list):
        for x in items[:limit]:
            if isinstance(x, dict):
                out.append(str(x.get("name", "")) + " | meta=" + str(x.get("meta_name","")))
            else:
                out.append(str(x))
    return out

def main():
    # JWT check
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT caducado</b>. Actualiza <b>CARDTRADER_JWT</b>.")
        sys.exit(1)
    r.raise_for_status()

    game_id = 1
    category_id = 1

    base_params = {"game_id": game_id, "category_id": category_id, "per_page": 50}

    # Probamos varios nombres típicos de búsqueda
    trials = [
        ("q", "The One Ring"),
        ("query", "The One Ring"),
        ("search", "The One Ring"),
        ("name", "The One Ring"),
        ("translated_name", "The One Ring"),
        ("meta_name", "the-one-ring"),
        ("slug", "the-one-ring"),
    ]

    lines = []
    lines.append("<b>🔎 Test búsqueda en /api/v2/blueprints</b>")
    lines.append("game_id=<code>1</code> category_id=<code>1</code>")
    lines.append("")

    for key, value in trials:
        params = dict(base_params)
        params[key] = value

        rr = ct_get("/api/v2/blueprints", params=params)
        status = rr.status_code

        if status != 200:
            lines.append(f"<b>{key}=...</b> → <code>{status}</code>")
            continue

        data = rr.json()
        n = len(data) if isinstance(data, list) else 0
        sample = pick_names(data, limit=3)

        # Heurística: si filtra, debería devolver menos que 50 y contener 'ring' en alguno
        contains = any(("ring" in s.lower()) for s in sample)

        lines.append(f"<b>{key}={value}</b> → <code>200</code> | items=<code>{n}</code> | sample_ring=<code>{contains}</code>")
        for s in sample:
            # escapamos < >
            s2 = s.replace("<","&lt;").replace(">","&gt;")
            lines.append("<code>" + s2[:120] + "</code>")
        lines.append("")

    msg = "\n".join(lines)
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...\n<i>(recortado)</i>"
    telegram_send(msg)

if __name__ == "__main__":
    main()
