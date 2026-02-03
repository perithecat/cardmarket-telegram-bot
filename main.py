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

def safe(s, n=120):
    return str(s).replace("<","&lt;").replace(">","&gt;")[:n]

def main():
    # JWT check
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT caducado</b>. Actualiza <b>CARDTRADER_JWT</b>.")
        sys.exit(1)
    r.raise_for_status()

    game_id = 1
    category_id = 1
    needle = "The One Ring"

    base = {"game_id": game_id, "category_id": category_id, "per_page": 100}

    trials = [
        ({"q": needle}, "q"),
        ({"query": needle}, "query"),
        ({"search": needle}, "search"),
        ({"name": needle}, "name"),
        ({"filter[name]": needle}, "filter[name]"),
        ({"filter[display_name]": needle}, "filter[display_name]"),
        ({"filter[meta_name]": "the-one-ring"}, "filter[meta_name]"),
        ({"filter[search]": needle}, "filter[search]"),
        ({"q[name_cont]": needle}, "q[name_cont]"),
        ({"q[name_i_cont]": needle}, "q[name_i_cont]"),
        ({"q[translated_name_cont]": needle}, "q[translated_name_cont]"),
        ({"q[meta_name_cont]": "one-ring"}, "q[meta_name_cont]"),
        ({"q[slug_cont]": "one-ring"}, "q[slug_cont]"),
    ]

    lines = []
    lines.append("<b>🔎 Buscar blueprint en /api/v2/blueprints</b>")
    lines.append("Objetivo: <code>The One Ring</code>")
    lines.append("")

    for extra_params, label in trials:
        params = dict(base)
        params.update(extra_params)

        rr = ct_get("/api/v2/blueprints", params=params)
        status = rr.status_code

        if status != 200:
            lines.append(f"<b>{label}</b> → <code>{status}</code>")
            continue

        data = rr.json()
        if not isinstance(data, list):
            lines.append(f"<b>{label}</b> → <code>200</code> pero respuesta no-lista: <code>{safe(data, 120)}</code>")
            continue

        # Contar coincidencias dentro del lote
        names = [str(x.get("name","")) for x in data if isinstance(x, dict)]
        hits = [n for n in names if "ring" in n.lower()]

        first = data[0] if data else {}
        first_name = first.get("name","") if isinstance(first, dict) else str(first)

        lines.append(f"<b>{label}</b> → <code>200</code> | items=<code>{len(data)}</code> | ring_hits=<code>{len(hits)}</code>")
        lines.append("<code>first: " + safe(first_name, 80) + "</code>")
        if hits:
            # enseñamos las 3 primeras coincidencias
            for h in hits[:3]:
                lines.append("<code>hit: " + safe(h, 80) + "</code>")
        lines.append("")

    msg = "\n".join(lines)
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...\n<i>(recortado)</i>"
    telegram_send(msg)

if __name__ == "__main__":
    main()
