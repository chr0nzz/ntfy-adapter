from flask import Flask, jsonify, request
import requests, time, os, json

app = Flask(__name__)
BASE_URL = os.environ.get("NTFY_URL")

def get_color(p):
    # Mapping ntfy priority to Homepage status colors
    # 5=red (error), 4=orange (warning), 3=blue (info)
    return {5: "error", 4: "warning", 3: "info", 2: "gray"}.get(p, "info")

@app.route('/notifications')
def get_notifications():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    
    base = BASE_URL.rstrip('/')
    url = f"{base}/{topic}/json?poll=1&since=all"
    try:
        res = requests.get(url, timeout=10)
        msgs = []
        for line in res.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                if data.get('event') == 'message':
                    l_time = time.localtime(data.get('time', 0))
                    msgs.append({
                        "time": time.strftime("%H:%M", l_time),
                        "message": data.get('message', ''),
                        "color": get_color(data.get('priority', 3))
                    })
        msgs.sort(key=lambda x: x['time'], reverse=True)
        return jsonify(msgs[:5])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
