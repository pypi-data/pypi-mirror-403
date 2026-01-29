"""Scheduler for automatic daily sign-ins."""

import logging
import time
from datetime import datetime
from typing import Callable, List

import pytz
import schedule

from .config import Account, Config

logger = logging.getLogger(__name__)


def get_local_time_for_account(account: Account) -> str:
    """
    Get the scheduled time in local timezone format.

    Args:
        account: Account with checkin_time configuration

    Returns:
        Time string in HH:MM format for the local timezone
    """
    tz = pytz.timezone(account.checkin_time.timezone)
    target_time = datetime.now(tz).replace(
        hour=account.checkin_time.hour,
        minute=account.checkin_time.minute,
        second=0,
        microsecond=0,
    )

    # Convert to local time
    local_tz = datetime.now().astimezone().tzinfo
    local_time = target_time.astimezone(local_tz)

    return local_time.strftime("%H:%M")


def schedule_account(
    account: Account,
    sign_in_func: Callable[[Account], None],
) -> None:
    """
    Schedule sign-in for a single account.

    Args:
        account: Account to schedule
        sign_in_func: Function to call for sign-in
    """
    scheduled_time = get_local_time_for_account(account)
    identifier = account.identifier or "Unknown"

    logger.info(f"Scheduling {identifier} at {scheduled_time} local time")

    schedule.every().day.at(scheduled_time).do(sign_in_func, account)


def run_scheduler(
    config: Config,
    sign_in_func: Callable[[Account], None],
) -> None:
    """
    Run the scheduler loop.

    Args:
        config: Configuration with accounts
        sign_in_func: Function to call for each sign-in
    """
    logger.info("Starting scheduler mode...")

    # Schedule all accounts
    for account in config.accounts:
        schedule_account(account, sign_in_func)

    # Run initial sign-in for all accounts
    logger.info("Running initial sign-in for all accounts...")
    for account in config.accounts:
        sign_in_func(account)

    # Main scheduler loop
    logger.info("Entering scheduler loop. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
