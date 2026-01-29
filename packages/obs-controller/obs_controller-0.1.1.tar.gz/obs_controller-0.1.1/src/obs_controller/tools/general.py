"""General OBS tools - version, stats, hotkeys."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register general OBS tools."""

    @mcp.tool()
    def obs_get_version() -> dict:
        """
        Get OBS version information.

        Returns version info including OBS version, WebSocket version,
        platform, and supported features.
        """
        with obs_client() as client:
            version = client.get_version()
            return {
                "obs_version": version.obs_version,
                "obs_web_socket_version": version.obs_web_socket_version,
                "platform": version.platform,
                "platform_description": version.platform_description,
                "supported_image_formats": version.supported_image_formats,
            }

    @mcp.tool()
    def obs_get_stats() -> dict:
        """
        Get OBS performance statistics.

        Returns CPU usage, memory usage, disk space, FPS, and frame statistics.
        """
        with obs_client() as client:
            stats = client.get_stats()
            return {
                "cpu_usage_percent": round(stats.cpu_usage, 2),
                "memory_usage_mb": round(stats.memory_usage, 2),
                "available_disk_space_gb": round(stats.available_disk_space / 1024, 2),
                "active_fps": round(stats.active_fps, 2),
                "average_frame_render_time_ms": round(stats.average_frame_render_time, 2),
                "render_skipped_frames": stats.render_skipped_frames,
                "render_total_frames": stats.render_total_frames,
                "output_skipped_frames": stats.output_skipped_frames,
                "output_total_frames": stats.output_total_frames,
                "web_socket_session_incoming_messages": stats.web_socket_session_incoming_messages,
                "web_socket_session_outgoing_messages": stats.web_socket_session_outgoing_messages,
            }

    @mcp.tool()
    def obs_get_hotkey_list() -> dict:
        """
        Get list of all available hotkeys in OBS.

        Returns a list of hotkey names that can be triggered.
        """
        with obs_client() as client:
            hotkeys = client.get_hotkey_list()
            return {"hotkeys": hotkeys.hotkeys}

    @mcp.tool()
    def obs_trigger_hotkey_by_name(hotkey_name: str) -> dict:
        """
        Trigger a hotkey by its name.

        Args:
            hotkey_name: The name of the hotkey to trigger.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_hotkey_by_name(hotkey_name)
            return {"success": True, "triggered_hotkey": hotkey_name}

    @mcp.tool()
    def obs_trigger_hotkey_by_key_sequence(
        key_id: str,
        shift: bool = False,
        control: bool = False,
        alt: bool = False,
        command: bool = False,
    ) -> dict:
        """
        Trigger a hotkey by key sequence.

        Args:
            key_id: The key identifier (e.g., "OBS_KEY_F1").
            shift: Whether Shift is pressed.
            control: Whether Control is pressed.
            alt: Whether Alt is pressed.
            command: Whether Command (Mac) is pressed.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_hotkey_by_key_sequence(
                key_id,
                pressShift=shift,
                pressCtrl=control,
                pressAlt=alt,
                pressCmd=command,
            )
            return {
                "success": True,
                "key_id": key_id,
                "modifiers": {
                    "shift": shift,
                    "control": control,
                    "alt": alt,
                    "command": command,
                },
            }

    # NOTE: obs_sleep is intentionally removed.
    # The OBS WebSocket Sleep request only works inside request batches
    # (SERIAL_REALTIME or SERIAL_FRAME mode), not as a standalone request.
    # See: https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#sleep

    @mcp.tool()
    def obs_call_vendor_request(
        vendor_name: str, request_type: str, request_data: dict | None = None
    ) -> dict:
        """
        Call a vendor-specific request.

        Args:
            vendor_name: Name of the vendor.
            request_type: Type of request.
            request_data: Optional request data.

        Returns the vendor response data.
        """
        with obs_client() as client:
            response = client.call_vendor_request(
                vendor_name, request_type, request_data or {}
            )
            return {
                "vendor_name": response.vendor_name,
                "request_type": response.request_type,
                "response_data": response.response_data,
            }
