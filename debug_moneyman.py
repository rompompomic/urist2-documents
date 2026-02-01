import requests
from bs4 import BeautifulSoup
import re
import difflib
from urllib.parse import quote_plus

def debug_search(query):
    print(f"=== SEARCHING: {query} ===")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    url = f"https://www.rusprofile.ru/search?query={quote_plus(query)}"
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        print(f"URL: {response.url}")
        soup = BeautifulSoup(response.text, "lxml")
        
        # Check title
        print(f"Title: {soup.title.get_text() if soup.title else 'No Title'}")

        # Check for INN on page (if redirected)
        clip_inn = soup.select_one('[id^="clip_inn"]')
        if clip_inn:
            print(f"Found INN on page: {clip_inn.get_text(strip=True)}")
        else:
            print("No INN element found (maybe list page?)")
            
        # Check list items
        items = soup.select("div.list-element")
        print(f"Found {len(items)} list items")
        for i, item in enumerate(items[:3]):
            name = item.select_one("a.list-element__title")
            name_text = name.get_text(strip=True) if name else "Unknown"
            print(f"  Item {i+1}: {name_text}")
            info = item.select("div.list-element__row-info span")
            for span in info:
                print(f"    {span.get_text()}")

    except Exception as e:
        print(f"Error: {e}")
    print("\n")

def debug_inn(inn):
    print(f"=== CHECKING INN: {inn} ===")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    url = f"https://www.rusprofile.ru/search?query={inn}"
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        print(f"URL: {response.url}")
        soup = BeautifulSoup(response.text, "lxml")
        h1 = soup.select_one("h1")
        print(f"H1: {h1.get_text(strip=True) if h1 else 'No H1'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search('ООО МФК "МаниМен"')
    debug_search('ООО МФК МаниМен')
