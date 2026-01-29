"""OBS WebSocket client wrapper with error handling."""

from contextlib import contextmanager
from typing import Generator

import obsws_python as obs
from obsws_python.error import OBSSDKError

from .config import settings


class OBSConnectionError(Exception):
    """Raised when unable to connect to OBS."""

    pass


class OBSRequestError(Exception):
    """Raised when an OBS request fails."""

    pass


def get_client() -> obs.ReqClient:
    """
    Create and return an OBS WebSocket client.

    Returns:
        obs.ReqClient: Connected OBS client.

    Raises:
        OBSConnectionError: If connection fails.
    """
    try:
        return obs.ReqClient(
            host=settings.host,
            port=settings.port,
            password=settings.password if settings.password else None,
            timeout=settings.timeout,
        )
    except ConnectionRefusedError:
        raise OBSConnectionError(
            f"Cannot connect to OBS at {settings.host}:{settings.port}. "
            "Is OBS running with WebSocket Server enabled? "
            "(Tools → WebSocket Server Settings)"
        )
    except Exception as e:
        if "authentication" in str(e).lower():
            raise OBSConnectionError(
                "OBS authentication failed. Check your OBS_PASSWORD environment variable."
            )
        raise OBSConnectionError(f"Failed to connect to OBS: {e}")


@contextmanager
def obs_client() -> Generator[obs.ReqClient, None, None]:
    """
    Context manager for OBS client connections.

    Usage:
        with obs_client() as client:
            scenes = client.get_scene_list()

    Yields:
        obs.ReqClient: Connected OBS client.

    Raises:
        OBSConnectionError: If connection fails.
    """
    client = get_client()
    try:
        yield client
    finally:
        client.disconnect()


def handle_obs_error(func):
    """
    Decorator to handle OBS SDK errors and convert them to friendly messages.

    Args:
        func: The function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OBSSDKError as e:
            raise OBSRequestError(f"OBS request failed: {e}")
        except OBSConnectionError:
            raise
        except Exception as e:
            raise OBSRequestError(f"Unexpected error: {e}")

    return wrapper
