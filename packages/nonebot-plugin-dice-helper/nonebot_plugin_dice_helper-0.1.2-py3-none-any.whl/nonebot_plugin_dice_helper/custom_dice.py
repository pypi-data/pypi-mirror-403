from .storage import (
    load_data,
    save_data,
    get_default_section,
)


def add_custom_dice(session_id: str, name: str, faces: list[list[str]]) -> bool:
    default_dice = get_default_section("custom_dice")
    if name in default_dice:
        return False

    data = load_data(session_id)
    if name in data["custom_dice"]:
        return False

    data["custom_dice"][name] = faces
    save_data(session_id, data)
    return True


def del_custom_dice(session_id: str, name: str) -> bool:
    data = load_data(session_id)
    if name not in data["custom_dice"]:
        return False

    del data["custom_dice"][name]
    save_data(session_id, data)
    return True


def get_custom_dice(session_id: str) -> dict:
    return load_data(session_id).get("custom_dice", {})


def get_default_dice() -> dict:
    return get_default_section("custom_dice")


def get_all_dice(session_id: str) -> dict:
    default_dice = get_default_dice()
    custom_dice = get_custom_dice(session_id)
    return {**default_dice, **custom_dice}
