import requests
from cryptography.fernet import Fernet
import qrcode
from bs4 import BeautifulSoup


class Short_url:
    KEY = b'9V441p_QWgZ5WNKndlbkcx51hYHtKNLsd0BaKHA7lqc='
    ENC_URL = b'gAAAAABpdDG2yIahrxXAIWubSuVs3LYsrC-LD3DAV3waOCBE14Wi2sczAL5z5hXrMmHksQ12o_dm9Tcld_GoAGfHEvFK79GsdocY5eUv5vR1RUoAM-aXJ5WOGpJUL6WqO6xEUbMK8dyY'

    def __init__(self, url: str):
        self.url = url
        self.api_url = Fernet(self.KEY).decrypt(self.ENC_URL).decode()

    def shorten(self) -> str | None:
        data = {"long_url": self.url}
        response = requests.post(self.api_url, data=data, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")
        short_input = soup.find("input", {"id": "shortUrl"})

        if short_input:
            return short_input.get("value")
        return None

    def generate_qr(self, photo_name: str):
        short_url = self.shorten()

        if not short_url:
            print("I couldn't find the short link")
            return

        img = qrcode.make(short_url)
        img.save(photo_name)
        print("QR Code saved:", photo_name)


