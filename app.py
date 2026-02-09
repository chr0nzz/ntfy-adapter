import re
from flask import Flask, jsonify, request
import requests
import datetime
import os
import json
import time
import logging
import emoji

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ntfy_adapter")

BASE_URL = os.environ.get("NTFY_URL")
NTFY_USER = os.environ.get("NTFY_USER")
NTFY_PASS = os.environ.get("NTFY_PASS")
EXPIRY_MAX = int(os.environ.get("EXPIRY_MAX", 48))
EXPIRY_HIGH = int(os.environ.get("EXPIRY_HIGH", 24))
EXPIRY_STANDARD = int(os.environ.get("EXPIRY_STANDARD", 12))
MAX_NOTIFICATIONS = int(os.environ.get("MAX_NOTIFICATIONS", 5))

def decode_unicode(s):
    if not s:
        return s
    s = s.replace("**U", "\\U").replace("**u", "\\u")
    if s.startswith("\\U") or s.startswith("\\u"):
        return s.encode("utf-8").decode("unicode_escape")
    return s

def normalize_emoji(s):
    if not s:
        return s
    if s.startswith("*") and s.endswith("*"):
        s = ":" + s.strip("*") + ":"
    return s

def decode_emoji(s):
    if not s:
        return s
    s = normalize_emoji(s)
    s = decode_unicode(s)
    if s.startswith(":") and s.endswith(":"):
        return emoji.emojize(s, language="alias")
    return s

EMOJI_MAX = decode_emoji(os.environ.get("EMOJI_MAX", "🚨"))
EMOJI_HIGH = decode_emoji(os.environ.get("EMOJI_HIGH", "⚠️"))
EMOJI_STANDARD = decode_emoji(os.environ.get("EMOJI_STANDARD", "✔️"))

CLOCK_MODE = os.environ.get("CLOCK_FORMAT", "24h").lower()

if CLOCK_MODE == "12h":
    TIME_STRFTIME = "%I:%M %p"
else:
    TIME_STRFTIME = "%H:%M"

app = Flask("ntfy_adapter")

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

logger.info("ntfy-adapter starting...")
logger.info(f"NTFY_URL={BASE_URL}")
logger.info(f"AUTH_ENABLED={'Yes' if NTFY_USER else 'No'}")
logger.info(f"MAX_NOTIFICATIONS={MAX_NOTIFICATIONS}")
logger.info(f"CLOCK_MODE={CLOCK_MODE}")
logger.info(f"EXPIRY_MAX={EXPIRY_MAX}, EXPIRY_HIGH={EXPIRY_HIGH}, EXPIRY_STANDARD={EXPIRY_STANDARD}")
logger.info(f"EMOJI_MAX={EMOJI_MAX}, EMOJI_HIGH={EMOJI_HIGH}, EMOJI_STANDARD={EMOJI_STANDARD}")

def redact_url(text):
    url_pattern = r'https?://[^\s,]+'
    return re.sub(url_pattern, " 🔗", text)

@app.route("/notifications")
def get_notifications():
    if not BASE_URL:
        return jsonify([])
    topic = request.args.get("topic")
    if not topic:
        return jsonify([])

    target_url = f"{BASE_URL.rstrip('/')}/{topic}/json"
    url_pattern = r'https?://[^\s,]+'

    try:
        params = {"poll": "1", "since": "48h"}
        auth = (NTFY_USER, NTFY_PASS) if NTFY_USER and NTFY_PASS else None
        
        response = requests.get(
            target_url, 
            params=params, 
            auth=auth, 
            timeout=15
        )

        response.raise_for_status()
        
        messages = []
        now = time.time()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if data.get("event") == "message":
                        priority = data.get("priority", 3)
                        raw_ts = data.get("time", 0)
                        raw_title = data.get("title", "")
                        raw_msg = data.get("message", "")

                        if priority >= 5:
                            limit_hrs = EXPIRY_MAX
                            prefix = EMOJI_MAX
                        elif priority == 4:
                            limit_hrs = EXPIRY_HIGH
                            prefix = EMOJI_HIGH
                        else:
                            limit_hrs = EXPIRY_STANDARD
                            prefix = EMOJI_STANDARD

                        if raw_ts > (now - (limit_hrs * 3600)):
                            dt = datetime.datetime.fromtimestamp(raw_ts)

                            found_urls = re.findall(url_pattern, raw_msg)
                            actual_url = found_urls[0] if found_urls else ""

                            clean_body = re.sub(url_pattern, "", raw_msg).strip()
                            clean_title = raw_title.strip()

                            full_display = f"{prefix}  {clean_title}▪️\n{clean_body}"

                            if len(full_display) > 200:
                                full_display = full_display[:197] + "..."
                            
                            if actual_url:
                                full_display += " 🔗"

                            messages.append({
                                "id": raw_ts,
                                "time": dt.strftime(TIME_STRFTIME),
                                "message": full_display,
                                "click_url": actual_url
                            })
                except Exception:
                    continue

        messages.sort(key=lambda x: x["id"], reverse=True)
        return jsonify(messages[:MAX_NOTIFICATIONS])
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify([])

if __name__ == "__main__":
    logger.info("🚀 ntfy-adapter: Development server starting...")
    app.run(host="0.0.0.0", port=5000, threaded=True)
else:
    logger.info("✅ ntfy-adapter: Server is UP and Ready to receive requests")
