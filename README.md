# 🔔 ntfy-adapter
---
A lightweight Python adapter that transforms ntfy.sh notification streams into a format compatible with the GetHomepage.dev dashboard dynamic-list customapi widget. It exposes a simple HTTP API that returns the last 5 notifications, with automatic priority-based formatting.
---

## ✨ Features
- **Priority-Based Emoji**: Maps ntfy priorities:
  - 🚨  **Urgent (5)** → (`danger`)
  - ⚠️ **High (4)** → (`warning`)
  - ✔️ **Normal (3)** → (`success`)
- **Timezone Support**: Displays notification times using your local clock via the `TZ` environment variable.
- **Efficient Filtering**: Automatically provides the last 5 notifications to keep your dashboard clean.
- **Notifications will expire every**:
  - 48 hours → (`danger`) | Urgent
  - 24 hours → (`warning`) | High
  - 12 hours → (`success`) | Normal

## 🖼️ Example of the Homepage widget in both dark and light modes.

<p align="center">
  <img src="images/dark.png" alt="Dark mode screenshot" width="45%">
  <img src="images/light.png" alt="Light mode screenshot" width="45%">
</p>

---

### 🚀 Installation & Setup

### 1. Prerequisites
- A running **ntfy** instance (e.g., `http://192.168.1.50:8080` or `https://ntfy.domain.com`).
- A running Homepage instance (`https://gethomepage.dev`)
- Update your **ntfy** Docker Compose file to enable caching:
```yaml
    environment:
      - NTFY_CACHE_FILE=/var/cache/ntfy/cache.db
      - NTFY_CACHE_DURATION=48h
    volumes:
      - /path-to/ntfy/var/cache/ntfy:/var/cache/ntfy
```
- **Docker** and **Docker Compose** installed.

#### 2. Deployment Methods

##### Option A: Docker Compose (Recommended)
Create a `docker-compose.yml` file:

```yaml
services:
  ntfy-adapter:
    image: ghcr.io/chr0nzz/ntfy-adapter:latest
    container_name: ntfy-adapter
    restart: unless-stopped
    environment:
      # Change to your NTFY ip:port or domain:port #
      - NTFY_URL=http://<YOUR_NTFY_IP>:<PORT>  
      ## Change to your local timezone ##
      - TZ=America/Toronto  
      ### Optional: Override Notification Expiry ###
      # - EXPIRY_MAX=24 #Default is 48 hours
      # - EXPIRY_HIGH=12 #Default is 24 hours
      # - EXPIRY_STANDARD=6 #Default is 12 hours
    ports:
      - "5000:5000"
```

Run the command:
```bash
docker compose up -d
```

##### Option B: Docker Run
Run the container with a single command:
```bash
docker run -d \
  --name ntfy-adapter \
  -p 5000:5000 \
  -e NTFY_URL="http://<YOUR_NTFY_IP>:<PORT>" \
  -e TZ="America/Toronto" \
  ghcr.io/chr0nzz/ntfy-adapter:latest
```
Override notification expiry:
```bash
docker run -d \
  --name ntfy-adapter \
  -p 5000:5000 \
  -e NTFY_URL="http://<YOUR_NTFY_IP>:<PORT>" \
  -e TZ="America/Toronto" \
  -e EXPIRY_MAX="24" \
  -e EXPIRY_HIGH="12" \
  -e EXPIRY_STANDARD="6" \
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

## 🏠 Homepage Widget Configuration
Add the following to your `services.yaml` file in Homepage:
You can add one widget per ntfy topic.

```yaml
- Notifications:
    # href: https://ntfy.domain.com/topic
    # icon: sh-ntfy
    widget:
      type: customapi
      # change to your adapter ip and NTFY topic #
      url: http://<ADAPTER_IP>:5000/notifications?topic=<YOUR_TOPIC>
      display: dynamic-list
      refreshInterval: 5000
      method: get
      mappings:
        name: time
        label: message
```

---

## ⚙️ Environment Variables
| Variable | Description | Example |
| :--- | :--- | :--- |
| `NTFY_URL` | The URL of your ntfy server | `http://192.168.1.10:8080` or `https://ntfy.domain.com` |
| `TZ` | Your local timezone for timestamps | `America/Toronto` |
| `EXPIRY_MAX` | Expiry time (hours) for Urgent notifications | `24` |
| `EXPIRY_HIGH` | Expiry time (hours) for High notifications | `12` |
| `EXPIRY_STANDARD` | Expiry time (hours) for Normal notifications | `6` |

## 🤝 Contributing
Issues and pull requests are welcome! Feel free to open a ticket if you have suggestions for new features.

## 📄 License
This project is licensed under the MIT License.
