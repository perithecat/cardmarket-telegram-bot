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

def snip(x, n=700):
    s = str(x)
    s = s.replace("<","&lt;").replace(">","&gt;")
    return s[:n] + ("..." if len(s) > n else "")

def main():
    # JWT check
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send("⚠️ <b>JWT caducado</b>. Actualiza <b>CARDTRADER_JWT</b>.")
        sys.exit(1)
    r.raise_for_status()

    blueprint_id = 240264

    tests = [
        (f"/api/v2/blueprints/{blueprint_id}", None),
        (f"/api/v2/blueprints/{blueprint_id}/products", None),
        (f"/api/v2/blueprints/{blueprint_id}/listings", None),
        (f"/api/v2/blueprints/{blueprint_id}/offers", None),
        (f"/api/v2/products", {"blueprint_id": blueprint_id, "per_page": 20}),
        (f"/api/v2/listings", {"blueprint_id": blueprint_id, "per_page": 20}),
        (f"/api/v2/offers", {"blueprint_id": blueprint_id, "per_page": 20}),
        (f"/api/v2/marketplace/products", {"blueprint_id": blueprint_id, "per_page": 20}),
        (f"/api/v2/marketplace/listings", {"blueprint_id": blueprint_id, "per_page": 20}),
    ]

    lines = []
    lines.append("<b>🔎 Test listings/precios</b>")
    lines.append(f"blueprint_id=<code>{blueprint_id}</code>")
    lines.append("")

    for path, params in tests:
        rr = ct_get(path, params=params)
        status = rr.status_code
        lines.append(f"<b>{path}</b> → <code>{status}</code>")
        if status == 200:
            try:
                js = rr.json()
                lines.append("<code>" + snip(js) + "</code>")
            except Exception:
                lines.append("<code>" + snip(rr.text) + "</code>")
        else:
            lines.append("<code>" + snip(rr.text) + "</code>")
        lines.append("")

    msg = "\n".join(lines)
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...\n<i>(recortado)</i>"
    telegram_send(msg)

if __name__ == "__main__":
    main()
