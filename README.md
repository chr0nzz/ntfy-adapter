# ntfy-adapter
A lightweight Flask adapter to display ntfy.sh notifications on the tHomepage dashboard with priority-based colors and local timestamps.

## Features
- **Priority Colors**: Urgent (Red), High (Orange), Normal (Blue).
- **Timezone Support**: Matches your local wall clock via the `TZ` variable.
- **Dynamic List**: Shows the last 5 notifications.

## Homepage Configuration
Add this to your `services.yaml`:
```yaml
- Notifications:
    widget:
      type: customapi
      url: http://adapter-ip:5000/notifications?topic=YOUR_TOPIC # use your actual ntfy url:ip if they are not on the same network as your homepage container
      display: dynamic-list
      mappings:
        name: time
        label: message
        color: color
        state: color
