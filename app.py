import re
from flask import Flask, jsonify, request
import requests
import datetime
import os
import json
import time

app = Flask(__name__)
BASE_URL = os.environ.get("NTFY_URL")
EXPIRY_MAX = int(os.environ.get("EXPIRY_MAX", 48))
EXPIRY_HIGH = int(os.environ.get("EXPIRY_HIGH", 24))
EXPIRY_STANDARD = int(os.environ.get("EXPIRY_STANDARD", 12))

def redact_url(text):
    url_pattern = r'https?://\S+'
    return re.sub(url_pattern, '[URL]', text)

@app.route('/notifications')
def get_notifications():
    if not BASE_URL:
        return jsonify([]) 
    topic = request.args.get('topic')
    if not topic:
        return jsonify([])

    target_url = f"{BASE_URL.rstrip('/')}/{topic}/json"
    
    try:
        params = {"poll": "1", "since": "48h"}
        response = requests.get(target_url, params=params, timeout=15)
        
        messages = []
        now = time.time()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if data.get('event') == 'message':
                        priority = data.get('priority', 3)
                        raw_ts = data.get('time', 0)
                        
                        if priority >= 5:
                            limit_hrs = EXPIRY_MAX
                            prefix = "🚨 "
                        elif priority == 4:
                            limit_hrs = EXPIRY_HIGH
                            prefix = "⚠️ " 
                        else:
                            limit_hrs = EXPIRY_STANDARD
                            prefix = "✔️ "
                        
                        if raw_ts > (now - (limit_hrs * 3600)):
                            dt = datetime.datetime.fromtimestamp(raw_ts)
                            
                            clean_msg = redact_url(data.get('message', ''))
                            if len(clean_msg) > 65:
                                clean_msg = clean_msg[:62] + "..."

                            messages.append({
                                "id": raw_ts, 
                                "time": dt.strftime("%H:%M"),
                                "message": f"{prefix}{clean_msg}"
                            })
                except:
                    continue
        
        messages.sort(key=lambda x: x['id'], reverse=True)
        return jsonify(messages[:5])
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
