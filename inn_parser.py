#!/usr/bin/env python3
import sys
import re
import requests
import click
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

BASE_URL = "https://www.rusprofile.ru/search?query="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


def fetch(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


# ===================== СПИСОК =====================
def parse_from_list(html: str) -> tuple[str | None, str | None]:
    """
    Берём ИНН и адрес ПЕРВОЙ компании в списке
    """
    soup = BeautifulSoup(html, "lxml")

    item = soup.select_one("div.list-element")
    if not item:
        return None, None

    # ИНН
    inn = None
    for span in item.select("div.list-element__row-info span"):
        m = re.search(r"ИНН[:\s]+(\d{10}|\d{12})", span.get_text())
        if m:
            inn = m.group(1)
            break

    # Адрес
    address_tag = item.select_one("div.list-element__address")
    address = address_tag.get_text(strip=True) if address_tag else None

    return inn, address


# ===================== КАРТОЧКА =====================
def parse_from_card(html: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(html, "lxml")

    # ---- ИНН ----
    inn = None

    # вариант copy_target
    inn_tag = soup.select_one('[id^="clip_inn"]')
    if inn_tag:
        text = inn_tag.get_text(strip=True)
        if text.isdigit():
            inn = text

    # fallback regex
    if not inn:
        m = re.search(r"ИНН[:\s]+(\d{10}|\d{12})", html)
        if m:
            inn = m.group(1)

    # ---- АДРЕС ----
    address = None

    address_tag = soup.select_one("#clip_address")
    if address_tag:
        address = address_tag.get_text(" ", strip=True)

    return inn, address


def parse_smart(session: requests.Session, query: str) -> tuple[str | None, str | None]:
    search_url = BASE_URL + quote_plus(query)
    html = fetch(session, search_url)

    # 1️⃣ Пробуем как список
    inn, address = parse_from_list(html)
    if inn or address:
        return inn, address

    # 2️⃣ Пробуем карточку из списка
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one("a.list-element__title")

    if link and link.get("href"):
        card_url = "https://www.rusprofile.ru" + link["href"]
        card_html = fetch(session, card_url)
        return parse_from_card(card_html)

    # 3️⃣ Прямой редирект / карточка
    return parse_from_card(html)


@click.command()
@click.argument("query", nargs=-1, required=True)
def main(query):
    """
    python inn_parser.py <Название компании>
    """
    company_name = " ".join(query)

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        inn, address = parse_smart(session, company_name)
    except requests.RequestException as e:
        print(f"HTTP ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    if not inn and not address:
        print("Данные не найдены", file=sys.stderr)
        sys.exit(2)

    if inn:
        print(f"ИНН: {inn}")
    if address:
        print(f"Адрес: {address}")


if __name__ == "__main__":
    main()
