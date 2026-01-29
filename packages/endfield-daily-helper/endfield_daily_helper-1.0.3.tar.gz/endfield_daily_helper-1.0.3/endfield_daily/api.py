"""API client for Arknights: Endfield daily attendance."""

import base64
import hashlib
import hmac
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# API URLs
ATTENDANCE_URL = "https://zonai.skport.com/web/v1/game/endfield/attendance"
ACCOUNT_TOKEN_URL = "https://web-api.skport.com/cookie_store/account_token"
OAUTH_GRANT_URL = "https://as.gryphline.com/user/oauth2/v2/grant"
USER_CHECK_URL = "https://zonai.skport.com/web/v1/user/check"
PLAYER_BINDING_URL = "https://zonai.skport.com/api/v1/game/player/binding"

# SKPORT app code for OAuth
SKPORT_APP_CODE = "6eb76d4e13aa36e6"

# Endfield game ID on SKPORT platform
ENDFIELD_GAME_ID = "3"

# Static headers for zonai.skport.com API
PLATFORM = "3"
VNAME = "1.0.0"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class SignInResult:
    """Result of a sign-in attempt."""
    success: bool
    message: str
    days_signed: Optional[int] = None
    today_reward: Optional[str] = None
    already_signed: bool = False


class EndfieldClient:
    """Client for interacting with the Endfield attendance API."""

    def __init__(self, cookie: str, user_agent: Optional[str] = None, token: Optional[str] = None, language: str = "en"):
        """
        Initialize the client.

        Args:
            cookie: Full cookie string from browser OR the SK_OAUTH_CRED_KEY value
            user_agent: Optional custom user agent
            token: Optional ACCOUNT_TOKEN value (httpOnly cookie - must be extracted from 
                   browser DevTools > Application > Cookies or Network tab)
            language: Language code for API responses (e.g., "en", "vi-vn", "zh-CN")
        """
        self.cookie = cookie.strip()
        self.user_agent = user_agent or USER_AGENT
        self.account_token = token  # This is the ACCOUNT_TOKEN httpOnly cookie value
        self.cred_token = None  # SK_OAUTH_CRED_KEY value for signed requests
        self.sign_token = None  # Token for computing signatures
        self.game_role = None  # Format: "gameId_roleId_serverId" for sk-game-role header
        self.language = language
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """Configure the session with headers."""
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://game.skport.com",
            "Referer": "https://game.skport.com/",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        })

    def _extract_cookie_value(self, name: str) -> Optional[str]:
        """Extract a specific cookie value from the cookie string."""
        pattern = rf'{name}=([^;]+)'
        match = re.search(pattern, self.cookie)
        return match.group(1) if match else None

    def _get_account_token(self) -> Optional[str]:
        """
        Get account token for OAuth authentication.
        
        The ACCOUNT_TOKEN is an httpOnly cookie that cannot be accessed via document.cookie.
        It must be provided directly via the 'token' parameter or extracted from browser DevTools.
        
        Returns:
            Account token string or None if not available
        """
        # First priority: use token if provided directly
        if self.account_token:
            logger.debug("Using provided ACCOUNT_TOKEN")
            return self.account_token
        
        # Second: try to extract from cookie string (in case user copied from DevTools Network tab)
        token_from_cookie = self._extract_cookie_value("ACCOUNT_TOKEN")
        if token_from_cookie:
            logger.debug("Found ACCOUNT_TOKEN in cookie string")
            return token_from_cookie
            
        # Third: try the cookie_store API (requires valid SK_OAUTH_CRED_KEY cookie)
        sk_oauth = self._extract_cookie_value("SK_OAUTH_CRED_KEY")
        if sk_oauth:
            try:
                # The cookie_store endpoint needs the SK_OAUTH_CRED_KEY cookie
                cookie_header = f"SK_OAUTH_CRED_KEY={sk_oauth}"
                hg_info = self._extract_cookie_value("HG_INFO_KEY")
                if hg_info:
                    cookie_header += f"; HG_INFO_KEY={hg_info}"
                
                response = self.session.get(
                    ACCOUNT_TOKEN_URL,
                    headers={"Cookie": cookie_header},
                    timeout=30
                )
                logger.debug(f"cookie_store response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0 and data.get("data", {}).get("content"):
                        logger.debug("Got ACCOUNT_TOKEN from cookie_store API")
                        return data["data"]["content"]
                    else:
                        logger.warning(f"cookie_store API returned: {data}")
                elif response.status_code == 401:
                    logger.error(
                        "401 Unauthorized from cookie_store API. "
                        "The SK_OAUTH_CRED_KEY cookie may be expired. "
                        "Please provide the ACCOUNT_TOKEN directly via the 'token' config option."
                    )
            except Exception as e:
                logger.debug(f"Failed to get account token from API: {e}")
        
        logger.error(
            "Could not obtain ACCOUNT_TOKEN. Please provide it via the 'token' config option. "
            "You can find it in browser DevTools > Application > Cookies > .skport.com > ACCOUNT_TOKEN"
        )
        return None

    def _refresh_oauth_token(self, account_token: str) -> Optional[str]:
        """
        Exchange account token for a fresh SK_OAUTH_CRED_KEY.
        
        This calls the OAuth grant endpoint to get a new credential token
        that can be used for authenticated API requests.
        
        Args:
            account_token: The ACCOUNT_TOKEN value
            
        Returns:
            New SK_OAUTH_CRED_KEY token (cred) or None on failure
        """
        try:
            response = self.session.post(
                OAUTH_GRANT_URL,
                json={
                    "token": account_token,
                    "appCode": SKPORT_APP_CODE,
                    "type": 0  # Type 0 for web OAuth
                },
                timeout=30
            )
            logger.debug(f"OAuth grant response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Response format: {"status": 0, "type": "A", "msg": "OK", "data": {"code": "..."}}
                if data.get("status") == 0 and data.get("data", {}).get("code"):
                    oauth_code = data["data"]["code"]
                    logger.debug(f"Got OAuth code: {oauth_code[:30]}...")
                    return oauth_code
                else:
                    logger.error(f"OAuth grant failed: {data}")
            else:
                logger.error(f"OAuth grant HTTP error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            logger.error(f"OAuth grant request failed: {e}")
        
        return None

    def _get_cred_from_oauth_code(self, oauth_code: str) -> Optional[str]:
        """
        Generate a cred (credential) from the OAuth code.
        
        The OAuth code from gryphline.com needs to be exchanged for a cred
        that can be used with zonai.skport.com API.
        
        Args:
            oauth_code: The OAuth code from grant endpoint
            
        Returns:
            The cred token or None on failure
        """
        try:
            # The OAuth code IS the cred for zonai.skport.com
            # It's used directly in the 'cred' header
            response = self.session.post(
                "https://zonai.skport.com/web/v1/user/auth/generate_cred_by_code",
                json={
                    "kind": 1,
                    "code": oauth_code
                },
                timeout=30
            )
            logger.debug(f"Generate cred response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data", {}).get("cred"):
                    cred = data["data"]["cred"]
                    logger.debug(f"Got cred: {cred[:30]}...")
                    return cred
                else:
                    logger.error(f"Generate cred failed: {data}")
            else:
                logger.error(f"Generate cred HTTP error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            logger.error(f"Generate cred request failed: {e}")
        
        return None

    def _compute_sign(self, path: str, timestamp: str, body: str = "") -> str:
        """
        Compute the signature for zonai.skport.com API requests.
        
        The signature is computed using HMAC-SHA256 with the sign_token as the key.
        Formula: sign = MD5(HMAC-SHA256(path + body + timestamp + headers_json, sign_token))
        
        Args:
            path: API path (e.g., "/web/v1/game/endfield/attendance")
            timestamp: Unix timestamp as string
            body: Request body as JSON string (empty for GET, "{}" for POST)
            
        Returns:
            Signature hex string
        """
        if not self.sign_token:
            logger.warning("No sign_token available, returning empty signature")
            return ""
        
        # Build the string to sign
        headers_dict = {
            "platform": PLATFORM,
            "timestamp": timestamp,
            "dId": "",  # Device ID, can be empty
            "vName": VNAME
        }
        headers_json = json.dumps(headers_dict, separators=(',', ':'))
        
        # Concatenate: path + body + timestamp + headers_json
        sign_string = f"{path}{body}{timestamp}{headers_json}"
        
        # Compute HMAC-SHA256
        hmac_result = hmac.new(
            self.sign_token.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # MD5 of the HMAC result
        sign = hashlib.md5(hmac_result.encode('utf-8')).hexdigest()
        
        logger.debug(f"Sign string: {sign_string[:100]}...")
        logger.debug(f"Computed sign: {sign}")
        
        return sign

    def _refresh_sign_token(self) -> bool:
        """
        Refresh the sign token by calling the auth/refresh endpoint.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.cred_token:
            logger.error("No cred_token available for refresh")
            return False
        
        try:
            timestamp = str(int(time.time()))
            
            response = self.session.get(
                "https://zonai.skport.com/web/v1/auth/refresh",
                headers={
                    "cred": self.cred_token,
                    "platform": PLATFORM,
                    "vname": VNAME,
                    "timestamp": timestamp,
                    "sk-language": self.language
                },
                timeout=30
            )
            
            logger.debug(f"Auth refresh response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data", {}).get("token"):
                    self.sign_token = data["data"]["token"]
                    logger.debug(f"Got sign_token: {self.sign_token[:30] if self.sign_token else 'None'}...")
                    return True
                else:
                    logger.error(f"Auth refresh failed: {data}")
            else:
                logger.error(f"Auth refresh HTTP error: {response.status_code}")
        except Exception as e:
            logger.error(f"Auth refresh request failed: {e}")
        
        return False

    def _get_player_binding(self) -> bool:
        """
        Get player binding info to determine the sk-game-role header.
        
        The sk-game-role format is: "gameId_roleId_serverId"
        For example: "3_4605473178_2"
        
        Returns:
            True if successful, False otherwise
        """
        if not self.cred_token:
            logger.error("No cred_token available for player binding")
            return False
        
        try:
            timestamp = str(int(time.time()))
            
            headers = {
                "cred": self.cred_token,
                "platform": PLATFORM,
                "vname": VNAME,
                "timestamp": timestamp,
                "sk-language": self.language
            }
            
            # Add sign if available
            if self.sign_token:
                path = "/api/v1/game/player/binding"
                sign = self._compute_sign(path, timestamp)
                headers["sign"] = sign
            
            response = self.session.get(
                PLAYER_BINDING_URL,
                headers=headers,
                timeout=30
            )
            
            logger.debug(f"Player binding response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data", {}).get("list"):
                    # Find endfield binding
                    for app in data["data"]["list"]:
                        if app.get("appCode") == "endfield" and app.get("bindingList"):
                            binding = app["bindingList"][0]  # Get first binding
                            default_role = binding.get("defaultRole") or (binding.get("roles", [{}])[0] if binding.get("roles") else None)
                            
                            if default_role:
                                role_id = default_role.get("roleId")
                                server_id = default_role.get("serverId")
                                
                                if role_id and server_id:
                                    self.game_role = f"{ENDFIELD_GAME_ID}_{role_id}_{server_id}"
                                    logger.debug(f"Got game role: {self.game_role}")
                                    return True
                    
                    logger.warning("No endfield binding found in response")
                else:
                    logger.error(f"Player binding failed: {data}")
            else:
                logger.error(f"Player binding HTTP error: {response.status_code}")
        except Exception as e:
            logger.error(f"Player binding request failed: {e}")
        
        return False

    def _get_cookie_header(self) -> str:
        """
        Build cookie header with SK_OAUTH_CRED_KEY and HG_INFO_KEY.
        
        Returns:
            Cookie header string
        """
        # Extract HG_INFO_KEY if present
        hg_info = self._extract_cookie_value("HG_INFO_KEY")
        sk_oauth = self._extract_cookie_value("SK_OAUTH_CRED_KEY") or self.cred_token
        
        # Build the cookie string with required cookies
        cookie_parts = []
        if sk_oauth:
            cookie_parts.append(f"SK_OAUTH_CRED_KEY={sk_oauth}")
        if hg_info:
            cookie_parts.append(f"HG_INFO_KEY={hg_info}")
        
        return "; ".join(cookie_parts)

    def sign_in(self) -> SignInResult:
        """
        Perform daily sign-in.

        The authentication flow:
        1. Get ACCOUNT_TOKEN (from config token, cookie string, or cookie_store API)
        2. Exchange ACCOUNT_TOKEN for OAuth code via OAuth grant
        3. Exchange OAuth code for cred via generate_cred_by_code
        4. Refresh sign token via auth/refresh
        5. Use cred and sign token to call the attendance API with signed headers

        Returns:
            SignInResult with success status and details
        """
        # Step 1: Get account token
        account_token = self._get_account_token()
        if not account_token:
            return SignInResult(
                success=False,
                message=(
                    "Could not obtain ACCOUNT_TOKEN. "
                    "Please provide it via the 'token' config option. "
                    "Find it in: Browser DevTools > Application > Cookies > .skport.com > ACCOUNT_TOKEN"
                )
            )
        
        logger.debug(f"Got account token: {account_token[:20]}...")
        
        # Step 2: Get OAuth code
        oauth_code = self._refresh_oauth_token(account_token)
        if not oauth_code:
            # Try with existing SK_OAUTH_CRED_KEY from cookie as cred
            existing_cred = self._extract_cookie_value("SK_OAUTH_CRED_KEY")
            if existing_cred:
                logger.warning("OAuth token refresh failed, trying with existing SK_OAUTH_CRED_KEY as cred")
                self.cred_token = existing_cred
            else:
                return SignInResult(
                    success=False,
                    message="Failed to get OAuth code. Please check if your ACCOUNT_TOKEN is valid."
                )
        else:
            # Step 3: Exchange OAuth code for cred
            cred = self._get_cred_from_oauth_code(oauth_code)
            if cred:
                self.cred_token = cred
            else:
                # Try using the oauth_code directly as cred (fallback)
                logger.warning("Failed to exchange OAuth code for cred, using OAuth code directly")
                self.cred_token = oauth_code
        
        logger.debug(f"Using cred: {self.cred_token[:30] if self.cred_token else 'None'}...")
        
        # Step 4: Refresh sign token
        if not self._refresh_sign_token():
            logger.warning("Failed to get sign token, proceeding without signature")
        
        # Step 4.5: Get player binding for sk-game-role header
        if not self._get_player_binding():
            logger.warning("Failed to get player binding, proceeding without sk-game-role")
        
        # Step 5: Make attendance request with signed headers
        logger.debug(f"Sending sign-in request to {ATTENDANCE_URL}")
        
        try:
            timestamp = str(int(time.time()))
            path = "/web/v1/game/endfield/attendance"
            
            headers = {
                "cred": self.cred_token,
                "platform": PLATFORM,
                "vname": VNAME,
                "timestamp": timestamp,
                "sk-language": self.language,
                "Content-Type": "application/json",
            }
            
            # Add sk-game-role if we have it
            if self.game_role:
                headers["sk-game-role"] = self.game_role
            
            # Compute and add signature
            if self.sign_token:
                sign = self._compute_sign(path, timestamp)
                headers["sign"] = sign
            
            # Send empty body (no JSON)
            response = self.session.post(
                ATTENDANCE_URL,
                headers=headers,
                timeout=30
            )
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")

            if response.status_code == 401:
                # Try one more time after refreshing tokens
                logger.warning("Got 401, attempting to refresh and retry...")
                if self._refresh_sign_token():
                    timestamp = str(int(time.time()))
                    headers["timestamp"] = timestamp
                    
                    # Recompute sign with new timestamp
                    if self.sign_token:
                        headers["sign"] = self._compute_sign(path, timestamp)
                    
                    response = self.session.post(
                        ATTENDANCE_URL,
                        headers=headers,
                        timeout=30
                    )
                    logger.debug(f"Retry response status: {response.status_code}")
                    logger.debug(f"Retry response body: {response.text}")

            # Try to parse JSON response even for non-200 status codes
            # The API returns JSON error messages for expected errors like "already signed"
            try:
                data = response.json()
                return self._parse_response(data, response.status_code)
            except ValueError:
                if response.status_code != 200:
                    return SignInResult(
                        success=False,
                        message=f"HTTP error: {response.status_code} - {response.text[:100]}"
                    )
                raise

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return SignInResult(
                success=False,
                message=f"Request failed: {str(e)}"
            )
        except ValueError as e:
            logger.error(f"Failed to parse response: {e}")
            return SignInResult(
                success=False,
                message=f"Invalid response format: {str(e)}"
            )

    def _parse_response(self, data: dict, status_code: int = 200) -> SignInResult:
        """Parse the API response."""
        code = data.get("code", -1)
        message = data.get("message", "Unknown response")

        if code == 0:
            result_data = data.get("data", {})
            return SignInResult(
                success=True,
                message="Sign-in successful!",
                days_signed=result_data.get("signInCount"),
                today_reward=self._format_reward(result_data.get("reward")),
            )
        # Handle "already signed" cases - various message formats from the API
        elif code == 1001 or code == 10001 or "already" in message.lower() or "do not sign in again" in message.lower() or "重复签到" in message or status_code == 403:
            return SignInResult(
                success=True,
                message="Already signed in today",
                already_signed=True,
            )
        elif code == 10002:
            return SignInResult(
                success=False,
                message="Authentication failed. Please refresh your cookie."
            )
        else:
            return SignInResult(
                success=False,
                message=f"Sign-in failed: {message} (code: {code})"
            )

    def _format_reward(self, reward: Optional[dict]) -> Optional[str]:
        """Format reward info for display."""
        if not reward:
            return None

        name = reward.get("name", "Unknown")
        count = reward.get("count", 1)
        return f"{name} x{count}"


def validate_cookie(cookie: str) -> bool:
    """
    Validate that the cookie/token string is potentially valid.

    Args:
        cookie: Cookie string or token value to validate

    Returns:
        True if the input appears valid
    """
    if not cookie or len(cookie) < 10:
        logger.warning("Cookie/token is empty or too short")
        return False
    
    # If it looks like a simple token (no = or ;), it's probably valid
    if "=" not in cookie and ";" not in cookie:
        logger.debug("Input appears to be a simple token value")
        return True
    
    # For cookie strings, check for expected keys
    if "SK_OAUTH_CRED_KEY" in cookie or "HG_INFO_KEY" in cookie or "ACCOUNT_TOKEN" in cookie:
        return True
    
    logger.warning("Cookie string doesn't contain expected keys (SK_OAUTH_CRED_KEY, HG_INFO_KEY, or ACCOUNT_TOKEN)")
    return False
