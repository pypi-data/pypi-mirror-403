from os import getenv
from pathlib import Path
from urllib.parse import urljoin


class QwakConstants:
    """
    Qwak Configuration settings
    """

    __CONTROL_PLANE_GRPC_ADDRESS_ENVAR_NAME: str = "CONTROL_PLANE_GRPC_ADDRESS"

    QWAK_HOME = (
        getenv("QWAK_HOME")
        if getenv("QWAK_HOME") is not None
        else f"{str(Path.home())}"
    )

    QWAK_CONFIG_FOLDER: str = f"{QWAK_HOME}/.qwak"

    QWAK_CONFIG_FILE: str = f"{QWAK_CONFIG_FOLDER}/config"

    QWAK_AUTHORIZATION_FILE: str = f"{QWAK_CONFIG_FOLDER}/auth"

    QWAK_DEFAULT_SECTION: str = "default"

    QWAK_AUTHENTICATION_URL = "https://grpc.qwak.ai/api/v1/authentication/qwak-api-key"

    QWAK_AUTHENTICATED_USER_ENDPOINT: str = urljoin(
        f"https://{getenv(__CONTROL_PLANE_GRPC_ADDRESS_ENVAR_NAME, 'grpc.qwak.ai')}",
        "api/v0/runtime/get-authenticated-user-context",
    )
