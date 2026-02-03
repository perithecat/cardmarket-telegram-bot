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

def short_snip(obj, limit=900):
    s = str(obj)
    return s[:limit] + ("..." if len(s) > limit else "")

def main():
    # 1) JWT check
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT caducado</b>. Actualiza el secreto <b>CARDTRADER_JWT</b>.")
        sys.exit(1)
    r.raise_for_status()

    # 2) Confirm MTG id
    r = ct_get("/api/v2/games")
    r.raise_for_status()
    games = r.json()
    mtg_id = None
    for g in games.get("array", []):
        if str(g.get("name", "")).lower() == "magic":
            mtg_id = g.get("id")
            break
    if mtg_id is None:
        telegram_send("⚠️ No encontré MTG en /games.")
        sys.exit(1)

    # 3) Probar endpoints típicos (sin adivinar)
    tests = [
        ("/api/v2/categories", {"game_id": mtg_id}),
        ("/api/v2/expansions", {"game_id": mtg_id}),
        ("/api/v2/blueprints", {"game_id": mtg_id}),
        ("/api/v2/blueprints/search", {"game_id": mtg_id, "q": "The One Ring"}),
        ("/api/v2/products/search", {"game_id": mtg_id, "q": "The One Ring"}),
    ]

    lines = []
    lines.append("<b>✅ CardTrader OK</b>")
    lines.append("MTG game_id: <code>" + str(mtg_id) + "</code>")
    lines.append("")
    lines.append("<b>🔎 Test de endpoints</b>")

    for path, params in tests:
        try:
            rr = ct_get(path, params=params)
            status = rr.status_code
            txt = ""
            js = None
            if status == 200:
                try:
                    js = rr.json()
                    txt = short_snip(js)
                except Exception:
                    txt = short_snip(rr.text)
            else:
                txt = short_snip(rr.text)
            lines.append("")
            lines.append("<b>" + path + "</b>  →  <code>" + str(status) + "</code>")
            lines.append("<code>" + txt.replace("<", "&lt;").replace(">", "&gt;") + "</code>")
        except Exception as e:
            lines.append("")
            lines.append("<b>" + path + "</b>  →  <code>EXCEPTION</code>")
            lines.append("<code>" + short_snip(str(e)).replace("<", "&lt;").replace(">", "&gt;") + "</code>")

    msg = "\n".join(lines)
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...\n<i>(recortado)</i>"
    telegram_send(msg)

if __name__ == "__main__":
    main()
