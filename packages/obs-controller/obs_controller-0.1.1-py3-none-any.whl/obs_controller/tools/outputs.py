"""Output tools (virtual camera, replay buffer)."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register output control tools."""

    @mcp.tool()
    def obs_list_outputs() -> dict:
        """
        Get list of available outputs.

        Returns list of outputs with their status.
        """
        with obs_client() as client:
            result = client.get_output_list()
            return {
                "outputs": [
                    {
                        "name": o["outputName"],
                        "kind": o["outputKind"],
                        "width": o["outputWidth"],
                        "height": o["outputHeight"],
                        "active": o["outputActive"],
                        "flags": o["outputFlags"],
                    }
                    for o in result.outputs
                ]
            }

    @mcp.tool()
    def obs_get_output_status(output_name: str) -> dict:
        """
        Get status of a specific output.

        Args:
            output_name: Name of the output.

        Returns output status including active, reconnecting, timecode, etc.
        """
        with obs_client() as client:
            result = client.get_output_status(output_name)
            return {
                "output_name": output_name,
                "active": result.output_active,
                "reconnecting": result.output_reconnecting,
                "timecode": result.output_timecode,
                "duration_seconds": result.output_duration,
                "congestion": result.output_congestion,
                "bytes": result.output_bytes,
                "skipped_frames": result.output_skipped_frames,
                "total_frames": result.output_total_frames,
            }

    @mcp.tool()
    def obs_toggle_output(output_name: str) -> dict:
        """
        Toggle an output on/off.

        Args:
            output_name: Name of the output.

        Returns the new output state.
        """
        with obs_client() as client:
            result = client.toggle_output(output_name)
            return {
                "output_name": output_name,
                "active": result.output_active,
            }

    @mcp.tool()
    def obs_start_output(output_name: str) -> dict:
        """
        Start an output.

        Args:
            output_name: Name of the output.

        Returns success status.
        """
        with obs_client() as client:
            client.start_output(output_name)
            return {"success": True, "output_name": output_name, "active": True}

    @mcp.tool()
    def obs_stop_output(output_name: str) -> dict:
        """
        Stop an output.

        Args:
            output_name: Name of the output.

        Returns success status.
        """
        with obs_client() as client:
            client.stop_output(output_name)
            return {"success": True, "output_name": output_name, "active": False}

    @mcp.tool()
    def obs_get_output_settings(output_name: str) -> dict:
        """
        Get settings of an output.

        Args:
            output_name: Name of the output.

        Returns output settings.
        """
        with obs_client() as client:
            result = client.get_output_settings(output_name)
            return {
                "output_name": output_name,
                "output_settings": result.output_settings,
            }

    @mcp.tool()
    def obs_set_output_settings(output_name: str, settings: dict) -> dict:
        """
        Set settings of an output.

        Args:
            output_name: Name of the output.
            settings: Settings to apply.

        Returns success status.
        """
        with obs_client() as client:
            client.set_output_settings(output_name, settings)
            return {
                "success": True,
                "output_name": output_name,
            }

    # Virtual Camera specific tools
    @mcp.tool()
    def obs_get_virtual_cam_status() -> dict:
        """
        Get virtual camera status.

        Returns whether virtual camera is active.
        """
        with obs_client() as client:
            result = client.get_virtual_cam_status()
            return {
                "active": result.output_active,
            }

    @mcp.tool()
    def obs_toggle_virtual_cam() -> dict:
        """
        Toggle virtual camera on/off.

        Returns new virtual camera state.
        """
        with obs_client() as client:
            result = client.toggle_virtual_cam()
            return {
                "active": result.output_active,
            }

    @mcp.tool()
    def obs_start_virtual_cam() -> dict:
        """
        Start virtual camera.

        Returns success status.
        """
        with obs_client() as client:
            client.start_virtual_cam()
            return {"success": True, "active": True}

    @mcp.tool()
    def obs_stop_virtual_cam() -> dict:
        """
        Stop virtual camera.

        Returns success status.
        """
        with obs_client() as client:
            client.stop_virtual_cam()
            return {"success": True, "active": False}

    # Replay Buffer specific tools
    @mcp.tool()
    def obs_get_replay_buffer_status() -> dict:
        """
        Get replay buffer status.

        Returns whether replay buffer is active.
        """
        with obs_client() as client:
            result = client.get_replay_buffer_status()
            return {
                "active": result.output_active,
            }

    @mcp.tool()
    def obs_toggle_replay_buffer() -> dict:
        """
        Toggle replay buffer on/off.

        Returns new replay buffer state.
        """
        with obs_client() as client:
            result = client.toggle_replay_buffer()
            return {
                "active": result.output_active,
            }

    @mcp.tool()
    def obs_start_replay_buffer() -> dict:
        """
        Start replay buffer.

        Returns success status.
        """
        with obs_client() as client:
            client.start_replay_buffer()
            return {"success": True, "active": True}

    @mcp.tool()
    def obs_stop_replay_buffer() -> dict:
        """
        Stop replay buffer.

        Returns success status.
        """
        with obs_client() as client:
            client.stop_replay_buffer()
            return {"success": True, "active": False}

    @mcp.tool()
    def obs_save_replay_buffer() -> dict:
        """
        Save current replay buffer to file.

        Returns success status and saved file path.
        """
        with obs_client() as client:
            result = client.save_replay_buffer()
            return {
                "success": True,
                "saved_replay_path": getattr(result, "saved_replay_path", None),
            }

    @mcp.tool()
    def obs_get_last_replay_buffer_replay() -> dict:
        """
        Get the path of the last saved replay.

        Returns the saved replay path.
        """
        with obs_client() as client:
            result = client.get_last_replay_buffer_replay()
            return {
                "saved_replay_path": result.saved_replay_path,
            }
