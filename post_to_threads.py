# post_to_threads.py
import os, sys, time, json
import requests

BASE = os.environ.get("THREADS_API_BASE", "https://graph.threads.net/v1.0")
USER_ID = os.environ.get("THREADS_USER_ID")
TOKEN = os.environ.get("THREADS_ACCESS_TOKEN")

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_BASE_SEC = float(os.environ.get("RETRY_BASE_SEC", "1.5"))
DRY_RUN = os.getenv("DRY_RUN", "").lower() == "true"

def log(*args):
    print("[threads-bot]", *args, flush=True)

def read_thread_file(path="thread.txt"):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = [b.strip() for b in content.split("---") if b.strip()]
    return parts

def _request_with_retry(method, url, **kwargs):
    last_err = None
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.request(method, url, timeout=30, **kwargs)
            if r.status_code >= 400:
                r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            wait = RETRY_BASE_SEC * (2 ** (attempt-1))
            log(f"HTTP error on attempt {attempt}: {e}; sleep {wait:.1f}s")
            time.sleep(wait)
    if last_err:
        raise last_err

def create_text_container(text, reply_to_id=None):
    url = f"{BASE}/{USER_ID}/threads"
    data = {"text": text, "access_token": TOKEN}
    if reply_to_id:
        data["reply_to_id"] = reply_to_id
    if DRY_RUN:
        log(f"[DRY_RUN] create container text={text[:50]!r} reply_to={reply_to_id}")
        return "dry_container_id", {}
    r = _request_with_retry("POST", url, data=data)
    j = r.json()
    creation_id = j.get("id") or j.get("creation_id")
    return creation_id, j

def publish_container(creation_id):
    url = f"{BASE}/{USER_ID}/threads_publish"
    data = {"creation_id": creation_id, "access_token": TOKEN}
    if DRY_RUN:
        log(f"[DRY_RUN] publish container {creation_id}")
        return {"id": "dry_post_id"}
    r = _request_with_retry("POST", url, data=data)
    j = r.json()
    return j

def extract_post_id(publish_response: dict):
    for key in ("id", "post_id", "thread_id", "published_post_id"):
        if publish_response.get(key):
            return publish_response[key]
    for key in ("post","thread","data"):
        if isinstance(publish_response.get(key), dict):
            inner = publish_response[key]
            for k in ("id","post_id","thread_id"):
                if inner.get(k):
                    return inner[k]
    return None

def post_thread(parts):
    if not USER_ID or not TOKEN:
        raise SystemExit("Нужны переменные окружения THREADS_USER_ID и THREADS_ACCESS_TOKEN")
    log("Starting publish…")

    first = parts[0]
    cid, _ = create_text_container(first)
    pub1 = publish_container(cid)
    root_id = extract_post_id(pub1)
    log("Root published:", root_id or "(id unknown)")

    parent_id = root_id
    for idx, p in enumerate(parts[1:], start=2):
        try:
            cid, _ = create_text_container(p, reply_to_id=parent_id)
            pub = publish_container(cid)
            new_id = extract_post_id(pub)
            parent_id = new_id or parent_id
            log(f"Part {idx} published:", new_id or "(id unknown)")
            time.sleep(1.2)
        except Exception as e:
            log(f"ERROR publishing part {idx}: {e} — продолжаем.")

    log("Done.")

if __name__ == "__main__":
    parts = read_thread_file()
    if not parts:
        print("thread.txt пустой — сначала сгенерируйте контент news_to_threads.py")
        sys.exit(1)

    if DRY_RUN:
        for i, p in enumerate(parts, 1):
            print(f"[DRY_RUN] Part {i}:\n{p}\n---")
        sys.exit(0)

    post_thread(parts)
