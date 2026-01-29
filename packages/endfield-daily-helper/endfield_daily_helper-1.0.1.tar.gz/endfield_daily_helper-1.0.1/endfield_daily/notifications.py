"""Discord webhook notifications for Endfield Daily Helper."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from .api import SignInResult
from .config import Notification

logger = logging.getLogger(__name__)


def send_discord_notification(
    webhook_url: str,
    result: SignInResult,
    account_identifier: Optional[str] = None,
) -> bool:
    """
    Send a Discord webhook notification.

    Args:
        webhook_url: Discord webhook URL
        result: Sign-in result to report
        account_identifier: Optional account name for identification

    Returns:
        True if notification sent successfully
    """
    if result.success:
        color = 0x00FF00  # Green
        title = "✅ Endfield Daily Sign-in Successful"
        if result.already_signed:
            color = 0xFFAA00  # Orange
            title = "🔄 Already Signed In Today"
    else:
        color = 0xFF0000  # Red
        title = "❌ Endfield Daily Sign-in Failed"

    embed = {
        "title": title,
        "color": color,
        "description": result.message,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Endfield Daily Helper"},
        "fields": [],
    }

    if account_identifier:
        embed["fields"].append({
            "name": "Account",
            "value": account_identifier,
            "inline": True,
        })

    if result.days_signed is not None:
        embed["fields"].append({
            "name": "Days Signed",
            "value": str(result.days_signed),
            "inline": True,
        })

    if result.today_reward:
        embed["fields"].append({
            "name": "Today's Reward",
            "value": result.today_reward,
            "inline": True,
        })

    payload = {"embeds": [embed]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            logger.debug("Discord notification sent successfully")
            return True
        else:
            logger.error(f"Discord webhook failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False


def notify_all(
    notifications: List[Notification],
    result: SignInResult,
    account_identifier: Optional[str] = None,
) -> None:
    """
    Send notifications to all configured channels.

    Args:
        notifications: List of notification configurations
        result: Sign-in result to report
        account_identifier: Optional account name
    """
    event_type = "success" if result.success else "failure"

    for notif in notifications:
        if event_type not in notif.on:
            logger.debug(f"Skipping notification (event {event_type} not in {notif.on})")
            continue

        if notif.type == "discord":
            send_discord_notification(
                notif.webhook_url,
                result,
                account_identifier,
            )
        else:
            logger.warning(f"Unknown notification type: {notif.type}")
