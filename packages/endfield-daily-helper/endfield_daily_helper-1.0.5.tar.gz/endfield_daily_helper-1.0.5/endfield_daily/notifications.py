"""Discord webhook notifications for Endfield Daily Helper."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from .api import SignInResult
from .config import Notification

logger = logging.getLogger(__name__)

# Endfield icon for thumbnail (from repo)
ENDFIELD_ICON = "https://raw.githubusercontent.com/chiraitori/endfield-daily-helper/main/icon/app_icon.png"
REPO_URL = "https://github.com/chiraitori/endfield-daily-helper"


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
    # Determine status and color
    if result.success:
        if result.already_signed:
            color = 0x5865F2  # Discord blurple
            status = "Already signed in today"
        else:
            color = 0x57F287  # Discord green
            status = "OK"
    else:
        color = 0xED4245  # Discord red
        status = f"Error: {result.message}"

    # Build embed in hoyo-daily-logins-helper style
    embed = {
        "author": {
            "name": "chiraitori/endfield-daily-helper",
            "url": REPO_URL,
        },
        "title": "Endfield Daily Helper",
        "description": status,
        "color": color,
        "thumbnail": {"url": ENDFIELD_ICON},
        "fields": [
            {
                "name": "Game",
                "value": "Arknights: Endfield",
                "inline": False,
            },
            {
                "name": "Account",
                "value": account_identifier or "Unknown",
                "inline": False,
            },
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Add total sign-in days
    if result.days_signed is not None:
        embed["fields"].append({
            "name": "Total Sign-in days",
            "value": str(result.days_signed),
            "inline": False,
        })

    # Add rewards
    if result.today_reward:
        embed["fields"].append({
            "name": "Rewards",
            "value": result.today_reward,
            "inline": False,
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
