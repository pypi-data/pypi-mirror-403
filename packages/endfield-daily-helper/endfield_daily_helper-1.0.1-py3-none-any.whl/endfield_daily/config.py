"""Configuration file handling for Endfield Daily Helper."""

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger(__name__)


@dataclass
class CheckinTime:
    """Configuration for when to run check-in."""
    hour: int = 0
    minute: int = 5
    timezone: str = "Asia/Shanghai"


@dataclass
class Notification:
    """Notification configuration."""
    type: str  # "discord"
    webhook_url: str
    on: List[str] = field(default_factory=lambda: ["success", "failure"])


@dataclass
class Account:
    """Account configuration."""
    cookie: str
    identifier: Optional[str] = None
    token: Optional[str] = None
    checkin_time: CheckinTime = field(default_factory=CheckinTime)
    report_on: List[str] = field(default_factory=lambda: ["success", "failure"])


@dataclass
class Config:
    """Main configuration."""
    accounts: List[Account] = field(default_factory=list)
    enable_scheduler: bool = False
    notifications: List[Notification] = field(default_factory=list)
    user_agent: Optional[str] = None
    debug: bool = False


def load_config(config_path: Path) -> Config:
    """
    Load configuration from a TOML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Parsed Config object
    """
    logger.debug(f"Loading config from {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    config_section = data.get("config", {})
    accounts_data = data.get("accounts", [])

    # Parse notifications
    notifications = []
    for notif in config_section.get("notifications", []):
        notifications.append(Notification(
            type=notif.get("type", "discord"),
            webhook_url=notif.get("webhook_url", ""),
            on=notif.get("on", ["success", "failure"]),
        ))

    # Parse accounts
    accounts = []
    for acc in accounts_data:
        checkin_time_data = acc.get("checkin_time", {})
        checkin_time = CheckinTime(
            hour=checkin_time_data.get("hour", 0),
            minute=checkin_time_data.get("minute", 5),
            timezone=checkin_time_data.get("timezone", "Asia/Shanghai"),
        )

        accounts.append(Account(
            cookie=acc.get("cookie", ""),
            identifier=acc.get("identifier"),
            token=acc.get("token"),
            checkin_time=checkin_time,
            report_on=acc.get("report_on", ["success", "failure"]),
        ))

    return Config(
        accounts=accounts,
        enable_scheduler=config_section.get("enable_scheduler", False),
        notifications=notifications,
        user_agent=config_section.get("user_agent"),
        debug=config_section.get("debug", False),
    )


def find_config_file() -> Optional[Path]:
    """
    Find configuration file in common locations.

    Returns:
        Path to config file if found, None otherwise
    """
    search_paths = [
        Path.cwd() / "endfield-daily-helper.toml",
        Path.cwd() / "config.toml",
        Path.home() / ".config" / "endfield-daily-helper" / "config.toml",
    ]

    for path in search_paths:
        if path.exists():
            logger.debug(f"Found config file: {path}")
            return path

    return None
