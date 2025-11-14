import requests
from urllib.parse import quote
import json
import re
from pathlib import Path

BASE_URL = "https://en.wiktionary.org/w/api.php"
HEADERS = {"User-Agent": "ProtoWordFetcher/1.0 (contact@example.com)"}
DATA_DIR = Path("data")
SCRAPES_DIR = DATA_DIR / "scrapes"
DATA_DIR.mkdir(exist_ok=True)
SCRAPES_DIR.mkdir(exist_ok=True)
WORKING_FILE = DATA_DIR / "working_list.txt"
LOG_FILE = DATA_DIR / "log.txt"
RESULTS_FILE = DATA_DIR / "results.json"

def load_list(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    return []

def save_list(path, lst):
    with open(path, "w", encoding="utf-8") as f:
        for item in sorted(set(lst)):
            f.write(item + "\n")

def fetch_entry(entry):
    title = f"Reconstruction:Proto-West_Germanic/{entry}"
    encoded_title = quote(title, safe=":/")
    params = {
        "action": "query",
        "format": "json",
        "titles": encoded_title,
        "prop": "extracts",
        "explaintext": True}

    response = requests.get(BASE_URL, params=params, headers=HEADERS)
    if response.status_code != 200:
        print(f"HTTP Error {response.status_code} for {entry}")
        return None

    data = response.json()
    pages = data["query"]["pages"]
    for _, p in pages.items():
        if "missing" in p:
            print(f"Entry '{entry}' not found.")
            return None
        return p.get("title"), p.get("extract", "")
    return None

def extract_words(text):
    matches = re.findall(r"(?im)^Latin:\s*([a-zA-Z\*\-]+)", text)
    if not matches:
        print("No working list entries found in this page.")
        return []
    seen = set()
    unique_words = [w for w in matches if not (w in seen or seen.add(w))]
    return unique_words

def save_words(text):
    matches = re.findall(r"(?im)^(?:Dutch):\s*([a-zA-Z\*\-]+)", text)
    if not matches:
        print("No Dutch words found in this page.")
        return []
    seen = set()
    unique_words = [w for w in matches if not (w in seen or seen.add(w))]
    return unique_words

def save_page(entry, title, extract):
    page_path = SCRAPES_DIR / f"{entry}.json"
    data = {"entry": entry, "title": title, "extract": extract}
    with open(page_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_entry(entry):
    log = load_list(LOG_FILE)

    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            all_results = json.load(f)
    else:
        all_results = {}

    if entry in log:
        print(f"Entry '{entry}' is already in the log")
        return

    print(f"Fetching '{entry}'")
    result = fetch_entry(entry)
    if not result:
        print(f"No page found...")
        return

    title, extract = result
    save_page(entry, title, extract)

    if not log:
        new_words = extract_words(extract)
        if new_words:
            save_list(WORKING_FILE, new_words)
            print(f"Saved {new_words} to working list")
            
        results = save_words(extract)
        if results:
            all_results[entry] = results
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump
                (all_results, f, ensure_ascii=False, indent=2)
            print(f"Saved {results} to results under '{entry}'")

    log.append(entry)
    save_list(LOG_FILE, log)
    print(f"Logged '{entry}' as processed.")


if __name__ == "__main__":
    entry = "fallijan"
    process_entry(entry)
