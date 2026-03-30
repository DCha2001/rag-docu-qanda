LOCAL_USER_ID = "local-user"


def get_current_user() -> str:
    """
    Local development auth — always returns a fixed user ID.
    No authentication required.
    """
    return LOCAL_USER_ID
