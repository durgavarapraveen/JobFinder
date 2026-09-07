"""
WhatsApp delivery via CallMeBot (free, personal use).

ONE-TIME SETUP (do this from the phone number that will RECEIVE messages):
  1. Save +34 644 84 71 89 as a contact (e.g. "CallMeBot").
  2. On WhatsApp, send this exact text to it:  I allow callmebot to send me messages
  3. You'll get a reply with your personal apikey (a number).
  4. Put your phone + apikey in env vars WHATSAPP_PHONE and CALLMEBOT_APIKEY.

Phone format: country code + number, no '+' and no spaces. e.g. 918655016964
Free tier: a handful of messages/min, plenty for one daily digest.
"""
import os
import time
import httpx

PHONE = os.environ.get("WHATSAPP_PHONE", "").strip()
APIKEY = os.environ.get("CALLMEBOT_APIKEY", "").strip()


def send(text: str) -> bool:
    if not PHONE or not APIKEY:
        print("!! WHATSAPP_PHONE / CALLMEBOT_APIKEY not set — printing instead:\n")
        print(text)
        return False
    # CallMeBot caps message length; chunk to be safe.
    chunks = _chunk(text, 3500)
    ok = True
    for i, ch in enumerate(chunks):
        try:
            r = httpx.get(
                "https://api.callmebot.com/whatsapp.php",
                params={"phone": PHONE, "text": ch, "apikey": APIKEY},
                timeout=30,
            )
            if r.status_code != 200 or "ERROR" in r.text.upper():
                print(f"  whatsapp chunk {i} failed: {r.status_code} {r.text[:120]}")
                ok = False
        except Exception as e:
            print(f"  whatsapp chunk {i} error: {e}")
            ok = False
        time.sleep(4)  # respect CallMeBot rate limit
    return ok


def _chunk(s, n):
    out, cur = [], ""
    for line in s.split("\n"):
        if len(cur) + len(line) + 1 > n:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        out.append(cur)
    return out or [s]
