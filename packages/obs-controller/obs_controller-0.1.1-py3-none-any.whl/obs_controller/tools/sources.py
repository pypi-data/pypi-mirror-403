"""Source tools (screenshots, source info)."""

import base64

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register source tools."""

    @mcp.tool()
    def obs_get_source_active(source_name: str) -> dict:
        """
        Get whether a source is active (visible in program or preview).

        Args:
            source_name: Name of the source.

        Returns video and screenshot active status.
        """
        with obs_client() as client:
            result = client.get_source_active(source_name)
            return {
                "source_name": source_name,
                "video_active": result.video_active,
                "video_showing": result.video_showing,
            }

    @mcp.tool()
    def obs_get_source_screenshot(
        source_name: str,
        image_format: str = "png",
        image_width: int | None = None,
        image_height: int | None = None,
        image_compression_quality: int = -1,
    ) -> dict:
        """
        Get a screenshot of a source as base64 encoded data.

        Args:
            source_name: Name of the source.
            image_format: Format (png, jpg, bmp).
            image_width: Optional width (maintains aspect ratio if only width specified).
            image_height: Optional height.
            image_compression_quality: Compression quality (-1 for default).

        Returns base64 encoded image data.
        """
        with obs_client() as client:
            result = client.get_source_screenshot(
                source_name,
                image_format,
                image_width,
                image_height,
                image_compression_quality,
            )
            return {
                "source_name": source_name,
                "image_format": image_format,
                "image_data": result.image_data,
            }

    @mcp.tool()
    def obs_save_source_screenshot(
        source_name: str,
        file_path: str,
        image_format: str = "png",
        image_width: int | None = None,
        image_height: int | None = None,
        image_compression_quality: int = -1,
    ) -> dict:
        """
        Save a screenshot of a source to a file.

        Args:
            source_name: Name of the source.
            file_path: Path to save the image.
            image_format: Format (png, jpg, bmp).
            image_width: Optional width (maintains aspect ratio if only width specified).
            image_height: Optional height.
            image_compression_quality: Compression quality (-1 for default).

        Returns success status and file path.
        """
        with obs_client() as client:
            result = client.save_source_screenshot(
                source_name,
                image_format,
                file_path,
                image_width,
                image_height,
                image_compression_quality,
            )
            return {
                "success": True,
                "source_name": source_name,
                "file_path": file_path,
                "image_data": result.image_data,
            }

    @mcp.tool()
    def obs_get_source_private_settings(source_name: str) -> dict:
        """
        Get private settings of a source.

        Args:
            source_name: Name of the source.

        Returns private settings.
        """
        with obs_client() as client:
            result = client.get_source_private_settings(source_name)
            return {
                "source_name": source_name,
                "private_settings": result.source_private_settings,
            }

    @mcp.tool()
    def obs_set_source_private_settings(source_name: str, settings: dict) -> dict:
        """
        Set private settings of a source.

        Args:
            source_name: Name of the source.
            settings: Private settings to set.

        Returns success status.
        """
        with obs_client() as client:
            client.set_source_private_settings(source_name, settings)
            return {
                "success": True,
                "source_name": source_name,
            }
