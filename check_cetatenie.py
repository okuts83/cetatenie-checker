import requests
from bs4 import BeautifulSoup
import os

URL = "https://cetatenie.just.ro/ordine-articolul-1-1/"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DATA_FILE = "last_date.txt"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": text})


def get_latest_date():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    pdf_links = []

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if ".pdf" in href:
            pdf_links.append(a.text.strip())

    if not pdf_links:
        return None

    return pdf_links[-1]


def read_last():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE) as f:
        return f.read().strip()


def save_last(date):
    with open(DATA_FILE, "w") as f:
        f.write(date)


latest = get_latest_date()
last = read_last()

print("Latest:", latest)
print("Saved:", last)

if latest and latest != last:
    send_telegram(f"Новая дата: {latest}")
    save_last(latest)
    print("Telegram sent")
else:
    print("No update")
