"""Stream control tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register streaming control tools."""

    @mcp.tool()
    def obs_get_stream_status() -> dict:
        """
        Get current streaming status.

        Returns streaming state, duration, bytes sent, and other stats.
        """
        with obs_client() as client:
            status = client.get_stream_status()
            return {
                "streaming": status.output_active,
                "reconnecting": status.output_reconnecting,
                "timecode": status.output_timecode,
                "duration_seconds": status.output_duration,
                "congestion": status.output_congestion,
                "bytes_sent": status.output_bytes,
                "skipped_frames": status.output_skipped_frames,
                "total_frames": status.output_total_frames,
            }

    @mcp.tool()
    def obs_toggle_stream() -> dict:
        """
        Toggle streaming on/off.

        Returns the new streaming state.
        """
        with obs_client() as client:
            result = client.toggle_stream()
            return {
                "streaming": result.output_active,
            }

    @mcp.tool()
    def obs_start_stream() -> dict:
        """
        Start streaming.

        Returns success status.
        """
        with obs_client() as client:
            client.start_stream()
            return {"success": True, "streaming": True}

    @mcp.tool()
    def obs_stop_stream() -> dict:
        """
        Stop streaming.

        Returns success status.
        """
        with obs_client() as client:
            client.stop_stream()
            return {"success": True, "streaming": False}

    @mcp.tool()
    def obs_send_stream_caption(caption_text: str) -> dict:
        """
        Send a caption to the stream (for closed captioning).

        Args:
            caption_text: The caption text to send.

        Returns success status.
        """
        with obs_client() as client:
            client.send_stream_caption(caption_text)
            return {"success": True, "caption_sent": caption_text}

    @mcp.tool()
    def obs_get_stream_service_settings() -> dict:
        """
        Get current stream service settings.

        Returns stream service type and settings.
        """
        with obs_client() as client:
            result = client.get_stream_service_settings()
            return {
                "stream_service_type": result.stream_service_type,
                "stream_service_settings": result.stream_service_settings,
            }

    @mcp.tool()
    def obs_set_stream_service_settings(
        stream_service_type: str, stream_service_settings: dict
    ) -> dict:
        """
        Set stream service settings.

        Args:
            stream_service_type: Type of stream service (e.g., "rtmp_custom").
            stream_service_settings: Settings dict (e.g., {"server": "rtmp://...", "key": "..."}).

        Returns success status.
        """
        with obs_client() as client:
            client.set_stream_service_settings(
                stream_service_type, stream_service_settings
            )
            return {
                "success": True,
                "stream_service_type": stream_service_type,
            }
