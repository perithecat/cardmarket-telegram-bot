import os
import requests
import sys

# --- Config fácil ---
GAME_ID = 1
CATEGORY_ID = 1
CARD_NAME = "The One Ring"
MAX_PRODUCTS = 200  # cuantos productos mirar como máximo

# Preferencias (puedes cambiar)
PREF_LANG = "en"
PREF_CONDITIONS = ["Near Mint", "Slightly Played", "Moderately Played", "Played", "Poor"]
PREF_FOIL = False


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


def ct_get(path, params=None):
    jwt = os.environ["CARDTRADER_JWT"].strip()
    headers = {"Authorization": "Bearer " + jwt}
    url = "https://api.cardtrader.com" + path
    return requests.get(url, headers=headers, params=params, timeout=30)


def require_jwt():
    r = ct_get("/api/v2/info")
    if r.status_code in (401, 403):
        telegram_send(
            "⚠️ <b>JWT caducado o sin permisos</b>\n"
            "CardTrader → Token JWT → copia uno nuevo\n"
            "GitHub → Settings → Secrets → actualiza <b>CARDTRADER_JWT</b>."
        )
        sys.exit(1)
    r.raise_for_status()


def find_blueprint_id_by_name(card_name):
    # CardTrader: /blueprints filtra por name ✅
    params = {
        "game_id": GAME_ID,
        "category_id": CATEGORY_ID,
        "name": card_name,
        "per_page": 50
    }
    r = ct_get("/api/v2/blueprints", params=params)
    r.raise_for_status()
    items = r.json()

    if not isinstance(items, list) or not items:
        return None, None

    # Elegimos el "más estándar" = el que NO tiene palabras tipo extended/borderless/etc en slug
    # Si no, cogemos el primero.
    def score(b):
        slug = str(b.get("slug", "")).lower()
        bad = ["borderless", "extended", "promo", "prerelease", "showcase", "surge", "serialized", "poster"]
        return sum(1 for w in bad if w in slug)

    items_sorted = sorted(items, key=score)
    best = items_sorted[0]
    return best.get("id"), best


def get_marketplace_products(blueprint_id):
    # Devuelve dict: { "blueprint_id": [products...] }
    params = {"blueprint_id": blueprint_id, "per_page": MAX_PRODUCTS}
    r = ct_get("/api/v2/marketplace/products", params=params)
    r.raise_for_status()
    data = r.json()

    # A veces la clave viene como string del id
    key = str(blueprint_id)
    return data.get(key, [])


def price_eur_from_cents(price_cents):
    try:
        return float(price_cents) / 100.0
    except Exception:
        return None


def matches_filters(p):
    if p.get("on_vacation") is True:
        return False

    props = p.get("properties_hash", {}) or {}

    # Idioma
    lang = str(props.get("mtg_language", "")).lower()
    if lang and lang != PREF_LANG:
        return False

    # Foil
    foil = props.get("mtg_foil", None)
    if foil is not None and bool(foil) != bool(PREF_FOIL):
        return False

    return True


def pick_best_min_price(products):
    # Filtramos por (lang, foil, no-vacation)
    filtered = [p for p in products if matches_filters(p)]
    if not filtered:
        return None, None

    # Recorremos condiciones en orden y buscamos el mínimo
    for cond in PREF_CONDITIONS:
        cond_group = []
        for p in filtered:
            props = p.get("properties_hash", {}) or {}
            if props.get("condition") == cond:
                cond_group.append(p)
        if cond_group:
            best = min(cond_group, key=lambda x: x.get("price_cents", 10**12))
            return best, cond

    # Si no hay condition conocida, mínimo global
    best = min(filtered, key=lambda x: x.get("price_cents", 10**12))
    return best, str((best.get("properties_hash", {}) or {}).get("condition", "¿?"))


def main():
    require_jwt()

    blueprint_id, blueprint = find_blueprint_id_by_name(CARD_NAME)
    if not blueprint_id:
        telegram_send("⚠️ No encontré blueprint para: <b>" + CARD_NAME + "</b>")
        return

    products = get_marketplace_products(blueprint_id)
    if not products:
        telegram_send(
            "⚠️ Encontré la carta pero no hay productos en marketplace.\n"
            "Carta: <b>" + CARD_NAME + "</b>\n"
            "blueprint_id: <code>" + str(blueprint_id) + "</code>"
        )
        return

    best_product, used_condition = pick_best_min_price(products)
    if not best_product:
        telegram_send(
            "⚠️ Hay productos pero ninguno cumple filtros (en / no foil / no vacation).\n"
            "Carta: <b>" + CARD_NAME + "</b>\n"
            "blueprint_id: <code>" + str(blueprint_id) + "</code>"
        )
        return

    price = price_eur_from_cents(best_product.get("price_cents"))
    currency = best_product.get("price_currency", "EUR")
    qty = best_product.get("quantity", 1)

    exp = best_product.get("expansion", {}) or {}
    exp_name = exp.get("name_en", "")
    exp_code = exp.get("code", "")

    msg = (
        "<b>💍 Precio mínimo (CardTrader)</b>\n\n"
        "<b>" + CARD_NAME + "</b>\n"
        "Set: <code>" + str(exp_code) + "</code> " + str(exp_name) + "\n"
        "Condición usada: <b>" + str(used_condition) + "</b>\n"
        "Idioma: <b>EN</b> | Foil: <b>No</b>\n\n"
        "✅ Min: <b>" + f"{price:.2f}" + " " + str(currency) + "</b>\n"
        "Cantidad (listing): <b>" + str(qty) + "</b>\n"
        "\n<i>Listo para Short: “Hoy The One Ring arranca desde " + f"{price:.2f}" + "€ (EN, " + str(used_condition) + ")”</i>"
    )

    telegram_send(msg)


if __name__ == "__main__":
    main()
