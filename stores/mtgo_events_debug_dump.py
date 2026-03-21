#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

URL = "https://mtgoupdate.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def main():
    print("Lade Seite:", URL)

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler beim Laden:", e)
        return

    html = resp.text
    print("\n=== SERVER HTML (erste 5000 Zeichen) ===\n")
    print(html[:5000])
    print("\n=== ENDE SERVER HTML ===\n")

    soup = BeautifulSoup(html, "html.parser")

    # Prüfen, ob day0 existiert
    day0 = soup.select_one("#day0")
    print("day0 gefunden:", bool(day0))

    # Prüfen, ob irgendein font-Tag existiert
    fonts = soup.select("font")
    print("Anzahl font-Tags:", len(fonts))

    # Prüfen, ob Script-Tags existieren
    scripts = soup.find_all("script")
    print("Anzahl script-Tags:", len(scripts))

    # Zeige die ersten 5 Script-Tags
    print("\n=== Erste 5 Script-Tags ===")
    for i, s in enumerate(scripts[:5]):
        print(f"\n--- Script {i} ---")
        print(s)

    # Prüfen, ob JSON im HTML steht
    if "{" in html and "}" in html:
        print("\nMöglicherweise JSON im HTML gefunden ({}-Klammern vorhanden).")
    else:
        print("\nKein JSON im HTML gefunden.")

    # Prüfen, ob Templates existieren
    templates = soup.find_all("template")
    print("Anzahl <template>-Tags:", len(templates))

    # Prüfen, ob Shadow DOM Hinweise existieren
    if "shadowRoot" in html or "attachShadow" in html:
        print("Shadow DOM Hinweise gefunden.")
    else:
        print("Keine Shadow DOM Hinweise gefunden.")

if __name__ == "__main__":
    main()
