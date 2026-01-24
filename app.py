from flask import Flask, jsonify, request
import requests
import datetime
import os

app = Flask(__name__)

# Base URL from Compose (e.g., https://ntfy.xyzlab.dev)
BASE_URL = os.environ.get("NTFY_URL", "https://ntfy.xyzlab.dev").rstrip('/')

@app.route('/notifications')
def get_notifications():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "No topic provided. Use ?topic=NAME"}), 400

    try:
        # Construct the full URL for the specific topic
        target_url = f"{BASE_URL}/{topic}/json"
        
        # poll=1: get history and close connection
        # since=all: get all available cached messages
        params = {"poll": "1", "since": "all"}
        
        response = requests.get(target_url, params=params, timeout=10)
        
        messages = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = requests.json.loads(line)
                if data.get('event') == 'message':
                    dt = datetime.datetime.fromtimestamp(data.get('time', 0))
                    messages.append({
                        "time": dt.strftime("%H:%M"), # Just HH:MM for cleaner look
                        "message": data.get('message', '')
                    })
            except:
                continue

        # Sort newest first and take top 5
        messages.sort(key=lambda x: x['time'], reverse=True)
        return jsonify(messages[:5])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
