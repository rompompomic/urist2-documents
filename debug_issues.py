
import difflib
from decimal import Decimal

def test_fuzzy_dedup():
    print("--- Testing Fuzzy Dedup ---")
    name1 = "Трумвират"
    name2 = "Триумвират"
    
    # Normalize (dummy implementation based on processor.py logic)
    def normalize(n):
        return n.replace('ООО', '').replace('МКК', '').strip('"«»').strip()

    n1 = normalize(name1)
    n2 = normalize(name2)
    
    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    print(f"'{n1}' vs '{n2}' ratio: {ratio}")
    
    assert ratio > 0.85, "Ratio should be high enough!"
    print("Fuzzy logic seems fine if names are clean.")

import requests
from bs4 import BeautifulSoup
import re

def test_inn_address_fetch(inn):
    print(f"\n--- Testing Address Fetch for INN {inn} ---")
    
    # Simulate fetch from zachestnyibiznes (as in processor.py)
    url = f"https://zachestnyibiznes.ru/search?query={inn}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if address is found
        # Looking for address pattern
        text = soup.get_text()
        # Simple check for relevant address parts
        if "Новосибирск" in text or "область" in text:
            print("Found some address-like text in page content.")
            
            # Try to extract specific address - simulating processor.py logic which might use regex or GPT
            # In processor.py: convert_inn_to_address uses various sources.
            
            # Let's inspect what the page actually returns for this INN
            # We might need to find the specific element
            address_elem = soup.find('span', itemprop="address")
            if address_elem:
                print(f"Found itemprop='address': {address_elem.get_text(strip=True)}")
            else:
                 # Try finding via text search near "Юридический адрес"
                 idx = text.find("Юридический адрес")
                 if idx != -1:
                     snippet = text[idx:idx+200]
                     print(f"Snippet near 'Юридический адрес': {snippet}")
                 else:
                     print("Could not find 'Юридический адрес' marker.")
                     
    except Exception as e:
        print(f"Error fetching: {e}")

if __name__ == "__main__":
    test_fuzzy_dedup()
    test_inn_address_fetch("5433975207")
