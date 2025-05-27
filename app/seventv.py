import requests

from .errors import CapacityError, ConflictError, EmoteNotFoundError, OtherError, RestError, UnprivilegedError
from .models import EmoteSet


ENDPOINT = "https://7tv.io/v4/gql"


def emote_set_from_id(emote_set_id: str) -> EmoteSet | None:
    """
    Fetch a 7tv emote set by its ID.

    Args:
        emote_set_id: The ID of the emote set to fetch.

    Returns:
        An EmoteSet object if found, otherwise None.

    Raises:
        `RestError`: If the request to fetch the emote set fails.
    """
    query = """
        query EmoteSetByID($id: Id!) {
            emoteSets {
                emoteSet(id: $id) {
                    capacity
                    id
                    name
                    emotes {
                        items {
                            emote {
                                defaultName
                                flags {
                                    private
                                }
                                id
                            }
                            alias
                            id
                        }
                        totalCount
                    }
                    owner {
                        editors {
                            editorId
                        }
                        id
                    }
                }
            }
        }
    """

    variables = {"id": emote_set_id}
    payload = {"query": query, "variables": variables}

    try:
        response = requests.post(url=ENDPOINT, json=payload)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RestError(f"Something went wrong while fetching an emote set (status: {e.response.status_code})") from e

    result = response.json()
    return EmoteSet.model_validate(result["data"]["emoteSets"]["emoteSet"])


def add_emote(token: str, emote_set_id: str, emote_id: str, emote_name: str | None = None) -> None:
    """
    Add an emote to a 7tv emote set.

    Args:
        token: The 7tv token.
        emote_set_id: The ID of the emote set to add the emote to.
        emote_id: The ID of the emote to add.
        emote_name: The name of the emote to add. If None, the emote's original name will be used.

    Raises:
        `RestError`: If the request fails.
        `UnprivilegedError`: If the user is not allowed to modify the emote set.
        `EmoteNotFoundError`: If the emote to add does not exist.
        `ConflictError`: If there is a conflicting emote in the emote set.
        `CapacityError`: If there is no space left in the emote set.
        `OtherError`: If some other GQL error occurs while adding an emote.
    """
    query = """
        mutation AddEmoteToSet($setId: Id! $emote: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $setId) {
                    addEmote(id: $emote) {
                        id
                    }
                }
            }
        }
    """

    variables = {
        "setId": emote_set_id,
        "emote": {"emoteId": emote_id, "alias": emote_name},
    }

    payload = {"query": query, "variables": variables}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url=ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RestError(f"Something went wrong while adding an emote: {e}") from e

    data = response.json()
    if "errors" in data:
        error = data["errors"][0]
        message = error["message"]
        extension = error.get("extensions")

        if "emote not found" in message.lower():
            raise EmoteNotFoundError

        if extension is None:
            raise OtherError(f"Something went wrong while adding an emote: {message}")

        code = extension["code"]
        message = extension["message"].removeprefix(code).strip()

        if extension.get("code") == "LACKING_PRIVILEGES":
            raise UnprivilegedError
        elif extension.get("code") == "BAD_REQUEST":
            raise ConflictError
        elif extension.get("code") == "LOAD_ERROR":
            raise CapacityError
        else:
            raise OtherError(f"Something went wrong while adding an emote: {message}")


def remove_emote(token: str, emote_set_id: str, emote_id: str) -> None:
    """
    Remove an emote from an emote set.

    Args:
        token: The 7tv token.
        emote_set_id: The ID of the emote set to remove the emote from.
        emote_id: The ID of the emote to remove.

    Raises:
        `RestError`: If the request fails.
        `UnprivilegedError`: If the user is not allowed to modify the emote set.
        `EmoteNotFoundError`: If the emote to remove does not exist in the emote set.
        `OtherError`: If some other GQL error occurs while adding an emote.
    """
    query = """
        mutation RemoveEmoteFromSet($setId: Id! $emote: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $setId) {
                    removeEmote(id: $emote) {
                        id
                    }
                }
            }
        }
    """

    variables = {
        "setId": emote_set_id,
        "emote": {"emoteId": emote_id},
    }

    payload = {"query": query, "variables": variables}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url=ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RestError(f"Something went wrong while removing an emote: {e}") from e

    data = response.json()
    if "errors" in data:
        error = data["errors"][0]
        message = error["message"]
        extension = error.get("extensions")

        if "emote not found" in message.lower():
            raise EmoteNotFoundError

        if extension is None:
            raise OtherError(f"Something went wrong while removing an emote: {message}")

        code = extension["code"]
        message = extension["message"].removeprefix(code).strip()

        if extension.get("code") == "LACKING_PRIVILEGES":
            raise UnprivilegedError
        else:
            raise OtherError(f"Something went wrong while removing an emote: {message}")
