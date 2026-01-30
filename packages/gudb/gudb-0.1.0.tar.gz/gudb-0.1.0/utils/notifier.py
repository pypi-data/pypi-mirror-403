import requests
import os

def send_alert(query, gain, fix_explanation):
    """Sends a formatted notification to a Discord Webhook."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    if not webhook_url:
        print("⚠️ Discord webhook URL not configured. Skipping notification.")
        return
    
    payload = {
        "embeds": [{
            "title": "🚀 AI Database Optimization Ready",
            "color": 3066993, # Green
            "fields": [
                {"name": "Slow Query", "value": f"```{query[:100]}...```", "inline": False},
                {"name": "Predicted Gain", "value": f"**{gain}% Faster**", "inline": True},
                {"name": "Gemini's Reason", "value": fix_explanation[:1000], "inline": False}
            ],
            "footer": {"text": "View full details on the Sentinel Dashboard"}
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 204:
            print("✅ Discord notification sent successfully")
        else:
            print(f"⚠️ Discord notification failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending Discord notification: {e}")