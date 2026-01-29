"""Recording control tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register recording control tools."""

    @mcp.tool()
    def obs_get_record_status() -> dict:
        """
        Get current recording status.

        Returns recording state, duration, bytes, and paused status.
        """
        with obs_client() as client:
            status = client.get_record_status()
            return {
                "recording": status.output_active,
                "paused": status.output_paused,
                "timecode": status.output_timecode,
                "duration_seconds": status.output_duration,
                "bytes_recorded": status.output_bytes,
            }

    @mcp.tool()
    def obs_toggle_record() -> dict:
        """
        Toggle recording on/off.

        Returns the new recording state and output path.
        """
        with obs_client() as client:
            result = client.toggle_record()
            return {
                "recording": result.output_active,
                "output_path": getattr(result, "output_path", None),
            }

    @mcp.tool()
    def obs_start_record() -> dict:
        """
        Start recording.

        Returns success status.
        """
        with obs_client() as client:
            client.start_record()
            return {"success": True, "recording": True}

    @mcp.tool()
    def obs_stop_record() -> dict:
        """
        Stop recording.

        Returns success status and the output file path.
        """
        with obs_client() as client:
            result = client.stop_record()
            return {
                "success": True,
                "recording": False,
                "output_path": result.output_path,
            }

    @mcp.tool()
    def obs_toggle_record_pause() -> dict:
        """
        Toggle recording pause on/off.

        Returns the new paused state.
        """
        with obs_client() as client:
            result = client.toggle_record_pause()
            return {
                "paused": result.output_paused,
            }

    @mcp.tool()
    def obs_pause_record() -> dict:
        """
        Pause recording.

        Returns success status.
        """
        with obs_client() as client:
            client.pause_record()
            return {"success": True, "paused": True}

    @mcp.tool()
    def obs_resume_record() -> dict:
        """
        Resume recording.

        Returns success status.
        """
        with obs_client() as client:
            client.resume_record()
            return {"success": True, "paused": False}

    @mcp.tool()
    def obs_split_record_file() -> dict:
        """
        Split the current recording file (creates a new file).

        Returns success status.
        """
        with obs_client() as client:
            client.split_record_file()
            return {"success": True, "message": "Recording file split"}

    @mcp.tool()
    def obs_create_record_chapter(chapter_name: str | None = None) -> dict:
        """
        Create a chapter marker in the recording.

        Args:
            chapter_name: Optional name for the chapter.

        Returns success status.
        """
        with obs_client() as client:
            client.create_record_chapter(chapter_name)
            return {
                "success": True,
                "chapter_name": chapter_name,
            }

    @mcp.tool()
    def obs_get_record_directory() -> dict:
        """
        Get the current recording directory.

        Returns the recording directory path.
        """
        with obs_client() as client:
            result = client.get_record_directory()
            return {
                "record_directory": result.record_directory,
            }

    @mcp.tool()
    def obs_set_record_directory(directory: str) -> dict:
        """
        Set the recording directory.

        Args:
            directory: Path to the recording directory.

        Returns success status.
        """
        with obs_client() as client:
            client.set_record_directory(directory)
            return {
                "success": True,
                "record_directory": directory,
            }
