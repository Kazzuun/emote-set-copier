import sys
import time

from app.seventv import add_emote, emote_set_from_id, remove_emote
from app.console import (
    print_info,
    print_success,
    print_warning,
    print_error,
    print_traceback,
    ask_question,
    ask_confirm,
    progress_bar,
)
from app.errors import CapacityError, ConflictError, EmoteNotFoundError, OtherError, RestError, UnprivilegedError
from app.models import EmoteSet, EmoteSetEmote
from app.utils import load_token, save_token, is_valid_id, user_id_from_token


def get_user_token_and_id() -> tuple[str, str]:
    """
    Get the user's 7tv token and user ID. If the token is already saved, load it.
    Otherwise, prompt the user for their token.

    Returns:
        A tuple containing the user's 7tv token and their user ID.
    """
    token_file_name = "token.txt"
    token = load_token(token_file_name)

    if token is not None:
        print_info(f"Loading token from {token_file_name}...")
        seventv_user_id = user_id_from_token(token)
        if seventv_user_id is not None:
            print_success(f"Token loaded from {token_file_name}.")
            return (token, seventv_user_id)

    while True:
        token = ask_question("What is your 7tv token?")
        if token == "":
            print_warning("Please provide a token.")
            continue

        seventv_user_id = user_id_from_token(token)
        if seventv_user_id is None:
            continue

        save = ask_confirm(f"Save the token to {token_file_name} for easy access?")
        if save:
            save_token(token, token_file_name)
            print_success(f"Token saved to {token_file_name}.")
        else:
            print_info("Token not saved.")

        return (token, seventv_user_id)


def get_origin_emote_set() -> EmoteSet:
    """
    Prompt the user for the ID of the emote set they want to copy from. THe origin emote set must not be empty.

    Returns:
        The EmoteSet object corresponding to the provided ID.
    """
    while True:
        emote_set_id = ask_question("What is the ID of the emote set you want to copy?")
        if not is_valid_id(emote_set_id):
            print_warning("Invalid ID format. Please provide a valid ID.")
            continue

        from_emote_set = emote_set_from_id(emote_set_id)
        if from_emote_set is None:
            print_warning("Origin emote set was not found. Please provide a valid ID.")
            continue

        if from_emote_set.emotes.total_count == 0:
            print_warning("Origin emote set has no emotes. Please provide a different ID.")
            continue

        print_success(
            f"Found origin emote set: '{from_emote_set.name}' ({from_emote_set.emotes.total_count}/{from_emote_set.capacity})"
        )
        return from_emote_set


def get_target_emote_set(origin_set: EmoteSet, seventv_user_id: str) -> EmoteSet:
    """
    Prompt the user for the ID of the emote set they want to copy into. The target emote set must not be the same as the origin emote set
    and the user must be an editor of the target emote set.

    Returns:
        The EmoteSet object corresponding to the provided ID.
    """
    while True:
        target_emote_set_id = ask_question("What is the ID of the emote set you want to copy into?")
        if not is_valid_id(target_emote_set_id):
            print_warning("Invalid ID format. Please provide a valid ID.")
            continue

        target_emote_set = emote_set_from_id(target_emote_set_id)
        if target_emote_set is None:
            print_warning("Target emote set was not found. Please provide a valid ID.")
            continue

        if target_emote_set.id == origin_set.id:
            print_warning("Target emote set cannot be the same as the origin emote set. Please provide a different ID.")
            continue

        if target_emote_set.owner.id != seventv_user_id and seventv_user_id not in target_emote_set.owner.editors:
            print_warning(
                "You are not an editor of the target emote set. Please provide a different ID or ask the owner to add you as an editor."
            )
            continue

        print_success(
            f"Found target emote set: '{target_emote_set.name}' ({target_emote_set.emotes.total_count}/{target_emote_set.capacity})"
        )
        return target_emote_set


def process_emotes_to_copy(from_emote_set: EmoteSet, target_emote_set: EmoteSet) -> list[EmoteSetEmote]:
    """
    Process the emotes to copy from the origin emote set to the target emote set.
    Filters out private emotes and emotes that are the exact same. Prompts the user whether to replace conflicting emotes
    and to include emotes that exceed the emote set capacity.

    Args:
        from_emote_set: The emote set to copy emotes from.
        target_emote_set: The emote set to copy emotes into.

    Returns:
        A list of EmoteSetEmote objects that can be copied to the target emote set. May include emotes that have conflicting names
        with existing emotes in the target emote set, depending on user input.
    """
    # Ignore private emotes
    non_private_emotes = [emote for emote in from_emote_set.emotes.items if not emote.data.flags.private]

    private = from_emote_set.emotes.total_count - len(non_private_emotes)
    if private > 0:
        print_info(
            f"Found {private} private emote{'s' if private != 1 else ''} in the origin emote set. They will be ignored."
        )

    # Ignore emotes that are the exact same in the target emote set
    new_emotes = [
        emote
        for emote in non_private_emotes
        if (emote.id, emote.alias) not in [(e.id, e.alias) for e in target_emote_set.emotes.items]
    ]
    exactly_same = len(non_private_emotes) - len(new_emotes)
    if exactly_same > 0:
        print_info(
            f"Found {exactly_same} emote{'s' if exactly_same != 1 else ''} that are exactly the same in the target emote set. They will be ignored."
        )

    # Ignore emotes that have the same name
    non_conflicting_emotes = [
        emote for emote in non_private_emotes if emote.alias not in [e.alias for e in target_emote_set.emotes.items]
    ]
    conflicting = len(new_emotes) - len(non_conflicting_emotes)
    if conflicting > 0:
        print_info(f"Found {conflicting} conflicting emote{'s' if conflicting != 1 else ''} in the target emote set.")
        force = ask_confirm(
            f"Do you want to replace {'them' if conflicting != 1 else 'it'} with the copied emote{'s' if conflicting != 1 else ''}?"
        )
        if force:
            non_conflicting_emotes = new_emotes

    # Ignore emotes that would exceed the target emote set's capacity
    space_available = target_emote_set.capacity - target_emote_set.emotes.total_count
    emotes_to_copy = len(non_conflicting_emotes)
    if space_available < emotes_to_copy:
        print_info(
            f"The number of emotes to be copied exceeds the space available in the target emote set ({emotes_to_copy}>{space_available})."
        )
        only_fitting = ask_confirm("Only add emotes that fit?", default=True)
        if only_fitting:
            non_conflicting_emotes = non_conflicting_emotes[:space_available]

    if len(non_conflicting_emotes) == 0:
        print_warning("There are no valid emotes left to copy. Exiting...")
        sys.exit(0)

    return non_conflicting_emotes


def copy_emotes(token: str, emotes_to_copy: list[EmoteSetEmote], target_emote_set: EmoteSet) -> None:
    """
    Copy emotes from the origin emote set to the target emote set.
    Handles the copying of emotes, including removing conflicting emotes from the target set
    before adding the new emotes. It uses a progress bar to show the copying process.

    Args:
        token: The user's 7tv token.
        emotes_to_copy: A list of EmoteSetEmote objects to copy to the target emote set.
        target_emote_set: The EmoteSet object to copy the emotes into.
    """
    total = len(emotes_to_copy)
    start = ask_confirm(f"There are {total} emotes to copy. Start the copying process?", default=True)
    if not start:
        sys.exit(0)

    with progress_bar("Copying emotes") as progress:
        task = progress.add_task("Copying", total=total)

        for emote in emotes_to_copy:
            skip_removal = False
            attempts = 0
            while True:
                try:
                    # All conflicting emotes should be removed before adding the new emote
                    conflicting_emote = next((e for e in target_emote_set.emotes.items if e.alias == emote.alias), None)
                    if conflicting_emote is not None and not skip_removal:
                        try:
                            remove_emote(token, target_emote_set.id, conflicting_emote.id)
                        except EmoteNotFoundError:
                            print_warning(
                                f"Emote '{conflicting_emote.alias}' not found in the target set. Skipping removal..."
                            )
                            skip_removal = True

                    add_emote(token, target_emote_set.id, emote.id, emote.alias)
                    break

                except (RestError, OtherError):
                    attempts += 1
                    if attempts >= 5:
                        print_error("Failed to copy emote set. Exiting...")
                        print_traceback()
                        sys.exit(1)

                    sleep_time = 45 - (15 if attempts > 1 else 0)
                    print_error(f"Failed to add emote '{emote.alias}'. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

                except EmoteNotFoundError:
                    print_warning(f"Emote '{emote.alias}' ({emote.id}) not found. Skipping...")
                    break

                except ConflictError:
                    print_warning(f"Unexpected conflict while adding emote '{emote.alias}'. Skipping...")
                    break

                except UnprivilegedError:
                    print_error("You don't have permission to modify the target emote set. Exiting...")
                    sys.exit(1)

                except CapacityError:
                    print_error("Target emote set is full. Cannot add more emotes. Exiting...")
                    sys.exit(0)

            progress.update(task, advance=1)

    print_success("All emotes successfully copied!")


def main():
    try:
        token, seventv_user_id = get_user_token_and_id()

        from_emote_set = get_origin_emote_set()
        target_emote_set = get_target_emote_set(from_emote_set, seventv_user_id)
        emotes_to_copy = process_emotes_to_copy(from_emote_set, target_emote_set)

        copy_emotes(token, emotes_to_copy, target_emote_set)

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception:
        print_traceback()
        sys.exit(1)


if __name__ == "__main__":
    main()
