"""Command-line interface for Endfield Daily Helper."""

import argparse
import logging
import os
import sys
from pathlib import Path

from . import __version__
from .api import EndfieldClient, SignInResult, validate_cookie
from .config import Account, Config, find_config_file, load_config
from .notifications import notify_all
from .scheduler import run_scheduler

logger = logging.getLogger("endfield_daily")


def setup_logging(debug: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def sign_in_account(
    account: Account,
    config: Config,
) -> SignInResult:
    """
    Perform sign-in for a single account.

    Args:
        account: Account to sign in
        config: Global configuration

    Returns:
        SignInResult
    """
    identifier = account.identifier or "Account"
    logger.info(f"Signing in: {identifier}")

    client = EndfieldClient(account.cookie, config.user_agent, account.token, config.language)
    result = client.sign_in()

    if result.success:
        if result.already_signed:
            logger.info(f"[{identifier}] Already signed in today")
        else:
            logger.info(f"[{identifier}] Sign-in successful!")
            if result.days_signed:
                logger.info(f"[{identifier}] Days signed: {result.days_signed}")
            if result.today_reward:
                logger.info(f"[{identifier}] Reward: {result.today_reward}")
    else:
        logger.error(f"[{identifier}] {result.message}")

    # Send notifications
    if config.notifications:
        event_type = "success" if result.success else "failure"
        if event_type in account.report_on:
            notify_all(config.notifications, result, account.identifier)

    return result


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="endfield-daily",
        description="Automatically claim Arknights: Endfield daily login rewards",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--cookie",
        help="Cookie string (backup method - use --token instead)",
        default=os.environ.get("ENDFIELD_COOKIE"),
    )

    parser.add_argument(
        "--token",
        help="ACCOUNT_TOKEN from browser cookies (DevTools > Application > Cookies > .skport.com)",
        default=os.environ.get("ENDFIELD_TOKEN"),
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to configuration file (TOML)",
        default=os.environ.get("ENDFIELD_CONFIG"),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
        default=os.environ.get("ENDFIELD_DEBUG", "").lower() in ("1", "true"),
    )

    parser.add_argument(
        "--identifier",
        help="Account identifier for logging",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.debug)

    # Try to load config file
    config = Config(debug=args.debug)
    config_path = args.config_file or find_config_file()

    if config_path and config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            config = load_config(config_path)
            if args.debug:
                config.debug = True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 1

    # If cookie/token provided via CLI, create a single account
    if args.token or args.cookie:
        cookie_value = args.cookie or ""
        token_value = args.token
        
        if not token_value and not validate_cookie(cookie_value):
            logger.warning("No token provided and cookie may be incomplete.")
            logger.warning("Use --token with your ACCOUNT_TOKEN for reliable authentication.")

        account = Account(
            cookie=cookie_value,
            identifier=args.identifier or "CLI Account",
            token=token_value,
        )
        config.accounts.append(account)

    # Validate we have accounts to process
    if not config.accounts:
        logger.error("No accounts configured!")
        logger.error("Provide credentials via --token or create a config file.")
        logger.error("")
        logger.error("To get your ACCOUNT_TOKEN:")
        logger.error("  1. Open https://game.skport.com/endfield/sign-in")
        logger.error("  2. Log in with your Hypergryph account")
        logger.error("  3. Open browser DevTools (F12) > Application tab")
        logger.error("  4. Click Cookies > .skport.com")
        logger.error("  5. Find ACCOUNT_TOKEN and copy its value")
        logger.error("  6. Run: endfield-daily --token=\"YOUR_TOKEN\"")
        return 1

    # Run in scheduler mode or one-shot
    if config.enable_scheduler:
        def sign_in_wrapper(account: Account) -> None:
            sign_in_account(account, config)

        run_scheduler(config, sign_in_wrapper)
    else:
        # One-shot mode: sign in all accounts
        all_success = True
        for account in config.accounts:
            result = sign_in_account(account, config)
            if not result.success:
                all_success = False

        return 0 if all_success else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
