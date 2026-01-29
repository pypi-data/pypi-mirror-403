"""Media playback control tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register media playback control tools."""

    @mcp.tool()
    def obs_get_media_input_status(input_name: str) -> dict:
        """
        Get status of a media input.

        Args:
            input_name: Name of the media input.

        Returns media state, duration, and cursor position.
        """
        with obs_client() as client:
            result = client.get_media_input_status(input_name)
            return {
                "input_name": input_name,
                "state": result.media_state,
                "duration_ms": result.media_duration,
                "cursor_ms": result.media_cursor,
            }

    @mcp.tool()
    def obs_set_media_input_cursor(input_name: str, cursor_ms: int) -> dict:
        """
        Set the cursor position of a media input.

        Args:
            input_name: Name of the media input.
            cursor_ms: Cursor position in milliseconds.

        Returns success status.
        """
        with obs_client() as client:
            client.set_media_input_cursor(input_name, cursor_ms)
            return {
                "success": True,
                "input_name": input_name,
                "cursor_ms": cursor_ms,
            }

    @mcp.tool()
    def obs_offset_media_input_cursor(input_name: str, offset_ms: int) -> dict:
        """
        Offset the cursor position of a media input.

        Args:
            input_name: Name of the media input.
            offset_ms: Offset in milliseconds (positive = forward, negative = backward).

        Returns success status.
        """
        with obs_client() as client:
            client.offset_media_input_cursor(input_name, offset_ms)
            return {
                "success": True,
                "input_name": input_name,
                "offset_ms": offset_ms,
            }

    @mcp.tool()
    def obs_trigger_media_input_action(input_name: str, action: str) -> dict:
        """
        Trigger a media action on an input.

        Args:
            input_name: Name of the media input.
            action: Action to trigger. One of:
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NONE
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT
                - OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(input_name, action)
            return {
                "success": True,
                "input_name": input_name,
                "action": action,
            }

    @mcp.tool()
    def obs_media_play(input_name: str) -> dict:
        """
        Play a media input.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "play",
            }

    @mcp.tool()
    def obs_media_pause(input_name: str) -> dict:
        """
        Pause a media input.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "pause",
            }

    @mcp.tool()
    def obs_media_stop(input_name: str) -> dict:
        """
        Stop a media input.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "stop",
            }

    @mcp.tool()
    def obs_media_restart(input_name: str) -> dict:
        """
        Restart a media input from the beginning.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "restart",
            }

    @mcp.tool()
    def obs_media_next(input_name: str) -> dict:
        """
        Go to next media in playlist.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "next",
            }

    @mcp.tool()
    def obs_media_previous(input_name: str) -> dict:
        """
        Go to previous media in playlist.

        Args:
            input_name: Name of the media input.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_media_input_action(
                input_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS"
            )
            return {
                "success": True,
                "input_name": input_name,
                "action": "previous",
            }
