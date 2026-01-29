import requests
from cryptography.fernet import Fernet
from bs4 import BeautifulSoup
class Short_url:
    def __init__(self, url):
        self.url = url
        KEY = b'9V441p_QWgZ5WNKndlbkcx51hYHtKNLsd0BaKHA7lqc='
        ENC_URL = b'gAAAAABpdDG2yIahrxXAIWubSuVs3LYsrC-LD3DAV3waOCBE14Wi2sczAL5z5hXrMmHksQ12o_dm9Tcld_GoAGfHEvFK79GsdocY5eUv5vR1RUoAM-aXJ5WOGpJUL6WqO6xEUbMK8dyY'
        url_short = Fernet(KEY).decrypt(ENC_URL).decode()
        data = {
            "long_url": url
        }
        response = requests.post(url_short, data=data)
        soup = BeautifulSoup(response.text, "html.parser")
        short_input = soup.find("input", {"id": "shortUrl"})
        if short_input:
            short_url = short_input.get("value")
            print("Short URL:", short_url)
        else:
            print("I couldn't find the short link")


