import requests
from bs4 import BeautifulSoup
from io import BytesIO
from pypdf import PdfReader
import re
import os

# ---------------- НАСТРОЙКИ ----------------

URL = "https://cetatenie.just.ro/ordine-articolul-1-1/"

SEARCH_TEXT = [
    "14584/2024", "30117/2024", "30114/2024"
]

# Telegram: используем переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # добавь в Secrets GitHub или в систему
CHAT_IDS = os.environ.get("CHAT_IDS", "")  # список через запятую: "3868227762,12345678"
CHAT_IDS = [c.strip() for c in CHAT_IDS.split(",") if c.strip()]

LAST_DATE_FILE = "last_date.txt"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# ---------------- TELEGRAM ----------------

def send_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message
            }
            r = session.post(url, data=data, timeout=20)
            print(f"Telegram to {chat_id}:", r.json())
        except Exception as e:
            print(f"Telegram error for {chat_id}:", e)

# ---------------- СОХРАНЕНИЕ ДАТЫ ----------------

def get_last_date():
    if os.path.exists(LAST_DATE_FILE):
        with open(LAST_DATE_FILE) as f:
            return f.read().strip()
    return None

def save_last_date(date):
    with open(LAST_DATE_FILE, "w") as f:
        f.write(date)

# ---------------- ПОЛУЧЕНИЕ ПОСЛЕДНЕЙ ДАТЫ ----------------

def get_latest_pdfs():
    r = session.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    latest_date = None
    pdfs = []

    for li in soup.select("li"):
        text = li.get_text()
        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
        if date_match:
            date = date_match.group()
            if latest_date is None:
                latest_date = date
            if date != latest_date:
                break
            for link in li.find_all("a", href=True):
                if ".pdf" in link["href"]:
                    href = link["href"]
                    if not href.startswith("http"):
                        href = "https://cetatenie.just.ro" + href
                    pdfs.append(href)
    return latest_date, pdfs

# ---------------- ПРОВЕРКА PDF ----------------

def check_pdf(url):
    r = session.get(url, timeout=60)
    reader = PdfReader(BytesIO(r.content))
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t
    found = [s for s in SEARCH_TEXT if s in text]
    return found

# ---------------- MAIN ----------------

def main():
    latest_date, pdfs = get_latest_pdfs()
    print("Latest date:", latest_date)
    last_checked = get_last_date()
    if latest_date == last_checked:
        print("Already checked this date")
        return
    for pdf in pdfs:
        print("Checking:", pdf)
        found = check_pdf(pdf)
        if found:
            message = f"Found {', '.join(found)}\n{pdf}"
            send_telegram(message)
            print("FOUND:", found)
    save_last_date(latest_date)

# ---------------- START ----------------

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_IDS:
        print("Error: BOT_TOKEN or CHAT_IDS not set in environment variables")
    else:
        main()
