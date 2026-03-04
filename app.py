import eventlet
eventlet.monkey_patch()

import re
from flask import Flask, jsonify, request, make_response, send_file, abort
from flask_cors import CORS
import requests
import datetime
import os
import json
import time
import logging
import emoji
from collections import defaultdict

EXT_DISPLAY_URL = os.environ.get("DISPLAY_URL", "http://localhost:5000")
EXT_ADAPTER_URL = os.environ.get("ADAPTER_URL", "http://localhost:5000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ntfy_adapter")

BASE_URL = os.environ.get("NTFY_URL")
NTFY_USER = os.environ.get("NTFY_USER")
NTFY_PASS = os.environ.get("NTFY_PASS")
EXPIRY_MAX = int(os.environ.get("EXPIRY_MAX", 48))
EXPIRY_HIGH = int(os.environ.get("EXPIRY_HIGH", 24))
EXPIRY_STANDARD = int(os.environ.get("EXPIRY_STANDARD", 12))
MAX_NOTIFICATIONS = int(os.environ.get("MAX_NOTIFICATIONS", 5))
CONFIG_FILE_PATH = os.environ.get("CONFIG_FILE", "config.json")
ENABLE_DISPLAY = os.environ.get("ENABLE_DISPLAY", "true").lower() == "true"

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
TIME_STRFTIME = "%I:%M %p" if CLOCK_MODE == "12h" else "%H:%M"

app = Flask("ntfy_adapter")
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

def load_app_config():
    config = {
        "emoji_max": EMOJI_MAX,
        "emoji_high": EMOJI_HIGH,
        "emoji_standard": EMOJI_STANDARD,
        "max_notifications": MAX_NOTIFICATIONS,
        "clock_mode": CLOCK_MODE,
        "theme": "dark",
        "auto_scroll": True,
        "api": {
            "host_ip": "",
            "port": "5000",
            "topic": "media",
            "refresh_rate": 10000
        }
    }
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                file_config = json.load(f)
                if "api" in file_config:
                    config["api"].update(file_config["api"])
                for k, v in file_config.items():
                    if k != "api":
                        config[k] = v
        except Exception as e:
            logger.error(f"Error reading {CONFIG_FILE_PATH}: {e}")
    return config

@app.route("/config")
def get_config():
    if not ENABLE_DISPLAY:
        abort(404)
    return jsonify(load_app_config()), 200

@app.route("/display")
def serve_display():
    if not ENABLE_DISPLAY:
        abort(404)
    if os.path.exists("display.html"):
        return send_file("display.html")
    else:
        return "display.html not found.", 404

logger.info("ntfy-adapter starting...")
logger.info(f"NTFY_URL={BASE_URL}")
logger.info(f"AUTH_ENABLED={'Yes' if NTFY_USER else 'No'}")
logger.info(f"MAX_NOTIFICATIONS={MAX_NOTIFICATIONS} (Per Topic)")
logger.info(f"CLOCK_MODE={CLOCK_MODE}")
logger.info(f"EXPIRY_MAX={EXPIRY_MAX}, EXPIRY_HIGH={EXPIRY_HIGH}, EXPIRY_STANDARD={EXPIRY_STANDARD}")
logger.info(f"EMOJI_MAX={EMOJI_MAX}, EMOJI_HIGH={EMOJI_HIGH}, EMOJI_STANDARD={EMOJI_STANDARD}")
logger.info(f"DISPLAY_ENABLED={ENABLE_DISPLAY}")

def redact_url(text):
    url_pattern = r'https?://[^\s,]+'
    return re.sub(url_pattern, " 🔗", text)

@app.route("/notifications", methods=['GET', 'OPTIONS'])
def get_notifications():
    if request.method == 'OPTIONS':
        return make_response('', 204)

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
            timeout=10,
            stream=True
        )
        response.raise_for_status()
        
        topic_groups = defaultdict(list)
        now = time.time()

        for line in response.iter_lines(chunk_size=1024):
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if data.get("event") == "message":
                        priority = data.get("priority", 3)
                        raw_ts = data.get("time", 0)
                        raw_title = data.get("title", "")
                        raw_msg = data.get("message", "")
                        topic_name = data.get("topic", "")

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

                            topic_groups[topic_name].append({
                                "id": raw_ts,
                                "time": dt.strftime(TIME_STRFTIME),
                                "message": full_display,
                                "topic": topic_name,
                                "click_url": actual_url
                            })
                except Exception:
                    continue

        final_messages = []
        for t_name in topic_groups:
            topic_groups[t_name].sort(key=lambda x: x["id"], reverse=True)
            final_messages.extend(topic_groups[t_name][:MAX_NOTIFICATIONS])

        final_messages.sort(key=lambda x: x["id"], reverse=True)
        return jsonify(final_messages)
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching from ntfy: {e}")
        return jsonify([])
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify([])

if __name__ == "__main__":
    logger.info("🚀 ntfy-adapter: Development server starting...")
    app.run(host="0.0.0.0", port=5000, threaded=True)
else:
    logger.info("✅ ntfy-adapter: Server is UP and Ready to receive requests")
    logger.info(f"🔗 Adapter URL: {EXT_ADAPTER_URL.rstrip('/')}")
    if ENABLE_DISPLAY:
        logger.info(f"🔗 Display URL: {EXT_DISPLAY_URL.rstrip('/')}/display")
    else:
        logger.info("ℹ️ Display UI is disabled (ENABLE_DISPLAY=false)")
