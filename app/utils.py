import base64
import binascii
import json
from pathlib import Path
import re
import time

from platformdirs import user_config_dir

from .console import print_warning

APP_NAME = "emote_set_copier"
CONFIG_DIR_PATH = Path(user_config_dir(APP_NAME))
TOKEN_FILE_PATH = CONFIG_DIR_PATH / "7tv_token.txt"


def load_token() -> str | None:
    """
    Load a token from a file.

    Args:
        filename: The name of the file where the token is stored.

    Returns:
        The token if found, otherwise None.
    """
    if not TOKEN_FILE_PATH.exists():
        return None

    with Path.open(TOKEN_FILE_PATH, "r") as file:
        token = file.readline().strip()

    return token if token else None


def save_token(token: str) -> None:
    """
    Save a token to a file.

    Args:
        token: The token to save.
        filename: The name of the file where the token is stored.
    """
    if not CONFIG_DIR_PATH.exists():
        CONFIG_DIR_PATH.mkdir(parents=True, exist_ok=True)

    with Path.open(TOKEN_FILE_PATH, "w") as file:
        file.write(token.strip())


def user_id_from_token(token: str) -> str | None:
    """
    Checks the validity of a 7tv token. The token must be in the format of a JWT.
    Prints an error message if the token is invalid or expired.

    Args:
        token: The 7tv token.

    Returns:
        The user ID the token belongs to if the token is valid, otherwise None.
    """
    try:
        token_payload = json.loads(base64.b64decode(token.split(".")[1] + "=="))
    except (IndexError, json.JSONDecodeError, binascii.Error):
        print_warning("Invalid token format.")
        return None

    expiration_time = token_payload.get("exp")
    seventv_user_id = token_payload.get("sub")

    if expiration_time is None or seventv_user_id is None:
        print_warning("Invalid token payload.")
        return None

    if int(expiration_time) < time.time():
        print_warning("Token has expired. Please provide a new token.")
        return None

    return seventv_user_id


def is_valid_id(id: str) -> bool:
    """
    Check if the given ID is a valid 7tv ID. It must be either in the old format (MongoDB ObjectID) or the new format (ULID).
    Also accepts "global" as a valid ID.

    Args:
        id: The ID to check.

    Returns:
        True if the ID is valid, otherwise False.
    """
    mongo_objectid = re.compile(r"^[0-9a-fA-F]{24}$")
    ulid = re.compile(r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")
    return bool(mongo_objectid.match(id)) or bool(ulid.match(id)) or id == "global"
