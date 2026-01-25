# 🔔 ntfy-adapter

A lightweight Python adapter that transforms **ntfy.sh** notification streams into a format perfectly compatible with the **GetHomepage.dev** dashboard `dynamic-list` widget. It automatically handles priority-based coloring and ensures timestamps match your local time.

---

## ✨ Features
- **Priority-Based Emoji**: Maps ntfy priorities to Homepage status colors:
  - 🚨  **Urgent (5)** → (`danger`)
  - ⚠️ **High (4)** → (`warning`)
  - ✔️ **Normal (3)** → (`sucsess`)
- **Timezone Support**: Displays notification times using your local clock via the `TZ` environment variable.
- **Efficient Filtering**: Automatically provides the last 5 notifications to keep your dashboard clean.
- Notifications will expire every
  - 48 hours → (`danger`)
  - 24 → (`warning`)
  - 12 → (`sucsess`)

---

## 🚀 Installation & Setup

### 1. Prerequisites
- A running **ntfy** instance (e.g., `http://192.168.1.50:8080`).
- **Docker** and **Docker Compose** installed.

### 2. Deployment Methods

#### Option A: Docker Compose (Recommended)
Create a `docker-compose.yml` file:

```yaml
services:
  ntfy-adapter:
    image: ghcr.io/chr0nzz/ntfy-adapter:latest
    container_name: ntfy-adapter
    restart: unless-stopped
    environment:
      - NTFY_URL=http://<YOUR_NTFY_IP>:<PORT>
      - TZ=America/Toronto  # Change to your local timezone
    ports:
      - "5000:5000"
```

Run the command:
```bash
docker compose up -d
```

#### Option B: Docker Run
Run the container with a single command:
```bash
docker run -d \
  --name ntfy-adapter \
  -p 5000:5000 \
  -e NTFY_URL="http://<YOUR_NTFY_IP>:<PORT>" \
  -e TZ="America/Toronto" \
  ghcr.io/chr0nzz/ntfy-adapter:latest
```

---

## 🛠 Build from Source
If you want to build the image yourself instead of pulling from a registry:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/chr0nzz/ntfy-adapter.git
   cd ntfy-adapter
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t ntfy-adapter:local .
   ```

3. **Run your local build**:
   ```bash
   docker run -d -p 5000:5000 -e NTFY_URL="http://<IP>:<PORT>" ntfy-adapter:local
   ```

---

## 🏠 Homepage Configuration
Add the following to your `services.yaml` file in Homepage:

```yaml
- Notifications:
    widget:
      type: customapi
      url: http://<ADAPTER_IP>:5000/notifications?topic=<YOUR_TOPIC>
      display: dynamic-list
      refreshInterval: 30000
      mappings:
        name: time
        label: message
        color: color
        state: color
```

---

## ⚙️ Environment Variables
| Variable | Description | Example |
| :--- | :--- | :--- |
| `NTFY_URL` | The URL of your ntfy server | `http://192.168.1.10:8080` |
| `TZ` | Your local timezone for timestamps | `Europe/London` |

## 🤝 Contributing
Issues and pull requests are welcome! Feel free to open a ticket if you have suggestions for new features.

## 📄 License
This project is licensed under the MIT License.
