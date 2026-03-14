# clean user info
def parse_user_info(data: dict) -> dict[str, str]:
    for key, val in data.items():
        if key in ["first_name", "last_name"]:
            data[key] = data[key].strip().title()

        if key in ["email", "username"]:
            data[key] = data[key].strip().lower()

    return data
