# preflight.py
import os, requests, sys
BASE = os.getenv("THREADS_API_BASE", "https://graph.threads.net/v1.0")
USER_ID = os.getenv("THREADS_USER_ID")
TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

def create_text_container(text):
    r = requests.post(f"{BASE}/{USER_ID}/threads",
                      data={"text": text, "access_token": TOKEN}, timeout=30)
    r.raise_for_status()
    return r.json().get("id")

if __name__ == "__main__":
    if not USER_ID or not TOKEN:
        sys.exit("Нет THREADS_USER_ID/THREADS_ACCESS_TOKEN")
    cid = create_text_container("preflight: проверка прав, не публиковать")
    print("OK: контейнер создан (publish не выполнялся). creation_id =", cid)
