import requests

urls = [
    "https://www.dd-munich.de/_api/wix-events/v1/events",
    "https://www.dd-munich.de/_api/wix-events-web/v1/events",
    "https://www.dd-munich.de/_api/wix-events-web/v1/event-list",
    "https://www.dd-munich.de/api/wix-events/v1/events",
    "https://www.dd-munich.de/api/events/v1/events",
    "https://www.dd-munich.de/wix/api/events/v1/events",
    "https://www.dd-munich.de/_api/events/v1/events",
]

headers = {"User-Agent": "Mozilla/5.0"}

for url in urls:
    print("Teste:", url)
    try:
        r = requests.get(url, headers=headers)
        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get("Content-Type"))
        print("Body (erste 200 Zeichen):", r.text[:200])
    except Exception as e:
        print("Fehler:", e)

    print("-" * 60)
