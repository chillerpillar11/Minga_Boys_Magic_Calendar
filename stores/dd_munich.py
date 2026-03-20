for t_node, title_node in zip(time_nodes, title_nodes):
    time_text = t_node.get_text(strip=True)
    title = title_node.get_text(strip=True)

    print("DEBUG DD TITLE:", repr(title))
    print("DEBUG DD TIME:", repr(time_text))

    # Zeitformat robust parsen
    # 18.30 → 18:30
    time_text = time_text.replace(".", ":")

    try:
        hour, minute = map(int, time_text.split(":"))
    except Exception as e:
        print("DEBUG DD PARSE ERROR:", time_text, e)
        continue

    start = base_date.replace(hour=hour, minute=minute)
    end = start + timedelta(hours=3)

    events.append({
        "title": title,
        "start": start,
        "end": end,
        "location": "Deck & Dice Munich",
        "url": url,
        "description": "",
    })
