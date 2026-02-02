import os
import pandas as pd
import requests
from requests_oauthlib import OAuth1

# -------- Telegram --------
def telegram_send(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=payload, timeout=20)
    r.raise_for_status()

# -------- Cardmarket --------
class CardmarketClient:
    def __init__(self):
        self.app_token = os.environ["CM_APP_TOKEN"]
        self.app_secret = os.environ["CM_APP_SECRET"]
        self.access_token = os.environ["CM_ACCESS_TOKEN"]
        self.access_token_secret = os.environ["CM_ACCESS_TOKEN_SECRET"]
        self.base_url = "https://api.cardmarket.com/ws/v2.0/output.json"

    def _auth(self, url):
        return OAuth1(
            self.app_token,
            client_secret=self.app_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
            realm=url
        )

    def get(self, path, params=None):
        url = f"{self.base_url}/{path}"
        r = requests.get(url, auth=self._auth(url), params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def search_card(self, name):
        params = {
            "search": name,
            "idGame": 1,
            "idLanguage": 1,
            "maxResults": 3,
            "exact": "true"
        }
        data = self.get("products/find", params)
        products = data.get("product", [])
        return products if isinstance(products, list) else [products]

    def lowest_price(self, product_id):
        data = self.get(f"articles/{product_id}", {"maxResults": 50})
        articles = data.get("article", [])
        articles = articles if isinstance(articles, list) else [articles]
        prices = []
        for a in articles:
            if a and "price" in a:
                try:
                    prices.append(float(a["price"]))
                except:
                    pass
        return min(prices) if prices else None

def main():
    cards = [
        "The One Ring",
        "Orcish Bowmasters",
        "Ragavan, Nimble Pilferer",
        "Sol Ring"
    ]

    cm = CardmarketClient()
    rows = []

    for name in cards:
        products = cm.search_card(name)
        if not products:
            continue
        p = products[0]
        price = cm.lowest_price(p["idProduct"])
        if price:
            rows.append((p["enName"], price))

    rows.sort(key=lambda x: x[1])

    lines = ["<b>📈 Cardmarket · Top diario</b>", ""]
    for i, (name, price) in enumerate(rows[:5], 1):
        lines.append(f"{i}. <b>{name}</b> — {price:.2f} €")

    telegram_send("\n".join(lines))

if __name__ == "__main__":
    main()
