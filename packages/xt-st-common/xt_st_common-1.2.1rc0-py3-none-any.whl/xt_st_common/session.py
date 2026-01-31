from pathlib import Path
from typing import List, Optional

import jwt
from streamlit import context

from xt_st_common.config import StreamlitBaseSettings

settings = StreamlitBaseSettings()


def get_session_headers():
    """Returns the request headers for the current streamlit session."""
    if settings.DEBUG and settings.DEBUG_MOCK_SESSION:
        return {
            "X-Forwarded-For": "130.116.147.135",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Port": "443",
            "Host": "fracg-ui.exploration.tools",
            "X-Amzn-Trace-Id": "Root=1-642250e6-3b44a7d41992a61831721a43",
            "X-Amzn-Oidc-Data": "eyJ0eXAiOiJKV1QiLCJraWQiOiI2NGYyMTU4MS01MzEzLTRiZTUtYTVlYi1hMjUxMDliYTE0NTIiLCJhbGciOiJFUzI1NiIsImlzcyI6Imh0dHBzOi8vY29nbml0by1pZHAuYXAtc291dGhlYXN0LTIuYW1hem9uYXdzLmNvbS9hcC1zb3V0aGVhc3QtMl9sQzZHVUtPZWoiLCJjbGllbnQiOiIyaDhzM2NsZWMxNWgyaDRydTZnaDQ3MzdxMyIsInNpZ25lciI6ImFybjphd3M6ZWxhc3RpY2xvYWRiYWxhbmNpbmc6YXAtc291dGhlYXN0LTI6NDQ0NDg4MzU3NTQzOmxvYWRiYWxhbmNlci9hcHAvazhzLXh0YXBwc3Byb2QtMmYxYjk5ZGMwZC9jMjJlNTYxOTY0NjU2Y2ExIiwiZXhwIjoxNjc5OTcwNjU0fQ==.eyJzdWIiOiJiNWFiY2QyMy00NGI0LTQ4OTctOGFlOS00N2U1YjM0ODRjYTUiLCJuYW1lIjoiQWxleCBIdW50IiwiZW1haWwiOiJhbGV4Lmh1bnRAY3Npcm8uYXUiLCJ1c2VybmFtZSI6Imh1bjIyMCIsImV4cCI6MTY3OTk3MDY1NCwiaXNzIjoiaHR0cHM6Ly9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tL2FwLXNvdXRoZWFzdC0yX2xDNkdVS09laiJ9.z7LBzOiuudjAToQJIxQNrOHvr_CgwtcHMJx0nsg7qcTKuFcna2GGcZGcMBal9KTnF6YEb-bVh8XmH3Y4lGR9SA==",  # noqa: E501
            "X-Amzn-Oidc-Identity": "b5abcd23-44b4-4897-8ae9-47e5b3484ca5",
            settings.ACCESS_TOKEN_KEY: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLmFwLXNvdXRoZWFzdC0yLmFtYXpvbmF3cy5jb20vRVhBTVBMRSIsImlhdCI6MTY3OTk4NzU3MSwiZXhwIjo0MDc4Mjc4NzcxLCJhdWQiOiJ3d3cuZXhhbXBsZS5jb20iLCJzdWIiOiIxMTExY2QyMy00NGI0LTQ4OTctOGFlOS00N2U1YjM0ODExMTEiLCJjb2duaXRvOmdyb3VwcyI6WyJhcHAtZnJhY2ciLCJQcm9qZWN0IEFkbWluaXN0cmF0b3IiXSwidmVyc2lvbiI6IjIiLCJjbGllbnRfaWQiOiIxMTExMTExMTExMTExMTExMTExMTExMTExMSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gb3BlbmlkIHByb2ZpbGUgZW1haWwiLCJ1c2VybmFtZSI6Inp6ejk5OSIsImp0aSI6IjExMTE0YTJhLWQ5NmEtMTExMS05MWNhLTlmMTBiNjE2MjVjZSIsImF1dGhfdGltZSI6IjE2Nzk5ODc1NzEiLCJvcmlnaW5fanRpIjoiM2E2MDQxNDAtMGQ5NC0xMTExLTExMTEtMDY0MzQ4MmMxMTExIn0.al-W2v2WgbeBpOvEY-p8KQAqjlUn1TMPvw5rgQtYe4o",  # noqa: E501
            "Upgrade": "websocket",
            "Connection": "upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",  # noqa: E501
            "Origin": "https://fracg-ui.exploration.tools",
            "Sec-Websocket-Version": "13",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Cookie": "",
            "Sec-Websocket-Key": "t7f+56WSS5xn+qdI4L4Yqg==",
            "Sec-Websocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-Websocket-Protocol": "streamlit",
        }

    return context.headers


def decode_jwt(raw_jwt: str, algorithms: Optional[List[str]] = None, options=None) -> dict:
    """
    Decode a JWT and return its values as a dictionary.

    `algorithms` defaults to `["ES256"]`
    `options` defaults to `{"verify_signature": False}`
    """
    if algorithms is None:
        algorithms = ["ES256"]
    if options is None:
        options = {"verify_signature": False}
    return jwt.decode(raw_jwt, algorithms=algorithms, options=options)


def get_user_id(allow_default=True):
    """
    Returns the current user id.

    allow_default:
        return "default-user" if user not found
    """

    headers = get_session_headers()
    if headers is not None:
        if settings.USER_KEY in headers:
            return headers[settings.USER_KEY]
        if settings.OIDC_TOKEN and settings.OIDC_TOKEN in headers:
            return decode_jwt(headers[settings.OIDC_TOKEN])["sub"]
        if "X-Goog-Authenticated-User-Id" in headers:
            return headers["X-Goog-Authenticated-User-Id"].split(":")[1]
        if headers is not None and "Authorization" in headers and headers["Authorization"].startswith("Bearer "):
            token = headers["Authorization"].split(" ")[1]
            if token:
                # Decode the JWT token to extract the email
                try:
                    return decode_jwt(token)["sub"]
                except jwt.DecodeError:
                    pass
    if allow_default:
        return "default-user"

    raise KeyError("X-Auth-Request-User not found in headers")


def get_user_email(allow_default=True):
    """Return the user's email address from headers, otherwise return the string "default-user"."""
    headers = get_session_headers()
    if headers is not None and settings.EMAIL_KEY in headers:
        return headers[settings.EMAIL_KEY]
    if headers is not None and "X-Goog-Authenticated-User-Email" in headers:
        return headers["X-Goog-Authenticated-User-Email"].split(":")[1]
    if headers is not None and settings.OIDC_TOKEN and settings.OIDC_TOKEN in headers:
        return decode_jwt(headers[settings.OIDC_TOKEN])["email"]
    if headers is not None and "Authorization" in headers and headers["Authorization"].startswith("Bearer "):
        token = headers["Authorization"].split(" ")[1]
        if token:
            # Decode the JWT token to extract the email
            try:
                return decode_jwt(token)["email"]
            except jwt.DecodeError:
                pass
    if allow_default:
        return "default-user@exploration.tools"

    raise KeyError("Email Key not found in headers")


def get_oidc_groups() -> List[str]:
    """Attempts to retrieve the OIDC groups from the headers (e.g. cognito:groups)."""
    headers = get_session_headers()
    if headers is None or settings.ACCESS_TOKEN_KEY not in headers:
        raise KeyError(f"{settings.ACCESS_TOKEN_KEY} not found in headers")
    access_tok = decode_jwt(headers[settings.ACCESS_TOKEN_KEY])
    return access_tok.get("cognito:groups", [])


def get_user_name(allow_default=True):
    """Return user's name from headers, otherwise return the string "default-user"."""
    headers = get_session_headers()

    if headers is not None and settings.OIDC_TOKEN and settings.OIDC_TOKEN in headers:
        return decode_jwt(headers[settings.OIDC_TOKEN])["name"]
    if headers is not None and "Authorization" in headers and headers["Authorization"].startswith("Bearer "):
        token = headers["Authorization"].split(" ")[1]
        if token:
            # Decode the JWT token to extract the email
            try:
                return decode_jwt(token)["name"]
            except jwt.DecodeError:
                pass
    if allow_default:
        return "default-user"

    raise KeyError("X-Amzn-Oidc-Data not found in headers")


def get_user_path() -> str:
    """Return path to local file storage for the user."""
    return str(Path(settings.DATA_DIR) / get_user_email())
