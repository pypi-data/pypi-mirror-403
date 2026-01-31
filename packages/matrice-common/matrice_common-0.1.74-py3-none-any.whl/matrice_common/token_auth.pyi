"""Auto-generated stub for module: token_auth."""
from typing import Any

from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log

# Classes
class AuthToken:
    # Implements a custom authentication scheme.

    def __init__(self: Any, access_key: Any, secret_key: Any, refresh_token: Any) -> None: ...

    def set_bearer_token(self: Any) -> Any:
        """
        Obtain an authentication bearer token using the provided refresh token.
        """
        ...

class RefreshToken:
    # Implements a custom authentication scheme.

    def __init__(self: Any, access_key: Any, secret_key: Any) -> None: ...

    def set_bearer_token(self: Any) -> Any:
        """
        Obtain a bearer token using the provided access key and secret key.
        """
        ...

