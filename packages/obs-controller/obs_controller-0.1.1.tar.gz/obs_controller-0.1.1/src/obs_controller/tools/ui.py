"""UI control tools (studio mode, projectors)."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register UI control tools."""

    @mcp.tool()
    def obs_get_studio_mode_enabled() -> dict:
        """
        Get whether studio mode is enabled.

        Returns studio mode status.
        """
        with obs_client() as client:
            result = client.get_studio_mode_enabled()
            return {
                "studio_mode_enabled": result.studio_mode_enabled,
            }

    @mcp.tool()
    def obs_set_studio_mode_enabled(enabled: bool) -> dict:
        """
        Enable or disable studio mode.

        Args:
            enabled: Whether to enable (True) or disable (False) studio mode.

        Returns success status.
        """
        with obs_client() as client:
            client.set_studio_mode_enabled(enabled)
            return {
                "success": True,
                "studio_mode_enabled": enabled,
            }

    @mcp.tool()
    def obs_open_input_properties_dialog(input_name: str) -> dict:
        """
        Open the properties dialog for an input.

        Args:
            input_name: Name of the input.

        Returns success status.
        """
        with obs_client() as client:
            client.open_input_properties_dialog(input_name)
            return {
                "success": True,
                "input_name": input_name,
            }

    @mcp.tool()
    def obs_open_input_filters_dialog(input_name: str) -> dict:
        """
        Open the filters dialog for an input.

        Args:
            input_name: Name of the input.

        Returns success status.
        """
        with obs_client() as client:
            client.open_input_filters_dialog(input_name)
            return {
                "success": True,
                "input_name": input_name,
            }

    @mcp.tool()
    def obs_open_input_interact_dialog(input_name: str) -> dict:
        """
        Open the interact dialog for an input (for browser sources, etc.).

        Args:
            input_name: Name of the input.

        Returns success status.
        """
        with obs_client() as client:
            client.open_input_interact_dialog(input_name)
            return {
                "success": True,
                "input_name": input_name,
            }

    @mcp.tool()
    def obs_get_monitor_list() -> dict:
        """
        Get list of available monitors.

        Returns list of monitors with their info.
        """
        with obs_client() as client:
            result = client.get_monitor_list()
            return {
                "monitors": [
                    {
                        "index": m["monitorIndex"],
                        "name": m["monitorName"],
                        "width": m["monitorWidth"],
                        "height": m["monitorHeight"],
                        "position_x": m["monitorPositionX"],
                        "position_y": m["monitorPositionY"],
                    }
                    for m in result.monitors
                ]
            }

    @mcp.tool()
    def obs_open_video_mix_projector(
        video_mix_type: str,
        monitor_index: int | None = None,
        projector_geometry: str | None = None,
    ) -> dict:
        """
        Open a video mix projector.

        Args:
            video_mix_type: Type of mix (OBS_WEBSOCKET_VIDEO_MIX_TYPE_PREVIEW,
                           OBS_WEBSOCKET_VIDEO_MIX_TYPE_PROGRAM,
                           OBS_WEBSOCKET_VIDEO_MIX_TYPE_MULTIVIEW).
            monitor_index: Monitor index for fullscreen (-1 for windowed).
            projector_geometry: Optional Qt geometry string for windowed mode.

        Returns success status.
        """
        with obs_client() as client:
            client.open_video_mix_projector(
                video_mix_type, monitor_index, projector_geometry
            )
            return {
                "success": True,
                "video_mix_type": video_mix_type,
                "monitor_index": monitor_index,
            }

    @mcp.tool()
    def obs_open_source_projector(
        source_name: str,
        monitor_index: int | None = None,
        projector_geometry: str | None = None,
    ) -> dict:
        """
        Open a source projector.

        Args:
            source_name: Name of the source to project.
            monitor_index: Monitor index for fullscreen (-1 for windowed).
            projector_geometry: Optional Qt geometry string for windowed mode.

        Returns success status.
        """
        with obs_client() as client:
            client.open_source_projector(source_name, monitor_index, projector_geometry)
            return {
                "success": True,
                "source_name": source_name,
                "monitor_index": monitor_index,
            }

    # Profile management
    @mcp.tool()
    def obs_get_profile_list() -> dict:
        """
        Get list of available profiles.

        Returns list of profiles and the current profile.
        """
        with obs_client() as client:
            result = client.get_profile_list()
            return {
                "current_profile": result.current_profile_name,
                "profiles": result.profiles,
            }

    @mcp.tool()
    def obs_set_current_profile(profile_name: str) -> dict:
        """
        Set the current profile.

        Args:
            profile_name: Name of the profile to switch to.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_profile(profile_name)
            return {
                "success": True,
                "profile_name": profile_name,
            }

    @mcp.tool()
    def obs_create_profile(profile_name: str) -> dict:
        """
        Create a new profile.

        Args:
            profile_name: Name for the new profile.

        Returns success status.
        """
        with obs_client() as client:
            client.create_profile(profile_name)
            return {
                "success": True,
                "profile_name": profile_name,
            }

    @mcp.tool()
    def obs_remove_profile(profile_name: str) -> dict:
        """
        Remove a profile.

        Args:
            profile_name: Name of the profile to remove.

        Returns success status.
        """
        with obs_client() as client:
            client.remove_profile(profile_name)
            return {
                "success": True,
                "removed_profile": profile_name,
            }

    @mcp.tool()
    def obs_get_profile_parameter(
        parameter_category: str, parameter_name: str
    ) -> dict:
        """
        Get a parameter from the current profile.

        Args:
            parameter_category: Category of the parameter.
            parameter_name: Name of the parameter.

        Returns the parameter value.
        """
        with obs_client() as client:
            result = client.get_profile_parameter(parameter_category, parameter_name)
            return {
                "parameter_category": parameter_category,
                "parameter_name": parameter_name,
                "parameter_value": result.parameter_value,
                "default_parameter_value": result.default_parameter_value,
            }

    @mcp.tool()
    def obs_set_profile_parameter(
        parameter_category: str, parameter_name: str, parameter_value: str
    ) -> dict:
        """
        Set a parameter in the current profile.

        Args:
            parameter_category: Category of the parameter.
            parameter_name: Name of the parameter.
            parameter_value: Value to set.

        Returns success status.
        """
        with obs_client() as client:
            client.set_profile_parameter(
                parameter_category, parameter_name, parameter_value
            )
            return {
                "success": True,
                "parameter_category": parameter_category,
                "parameter_name": parameter_name,
            }

    # Scene collection management
    @mcp.tool()
    def obs_get_scene_collection_list() -> dict:
        """
        Get list of available scene collections.

        Returns list of scene collections and the current one.
        """
        with obs_client() as client:
            result = client.get_scene_collection_list()
            return {
                "current_scene_collection": result.current_scene_collection_name,
                "scene_collections": result.scene_collections,
            }

    @mcp.tool()
    def obs_set_current_scene_collection(collection_name: str) -> dict:
        """
        Set the current scene collection.

        Args:
            collection_name: Name of the scene collection to switch to.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_scene_collection(collection_name)
            return {
                "success": True,
                "scene_collection": collection_name,
            }

    @mcp.tool()
    def obs_create_scene_collection(collection_name: str) -> dict:
        """
        Create a new scene collection.

        Args:
            collection_name: Name for the new scene collection.

        Returns success status.
        """
        with obs_client() as client:
            client.create_scene_collection(collection_name)
            return {
                "success": True,
                "scene_collection": collection_name,
            }

    # Video settings
    @mcp.tool()
    def obs_get_video_settings() -> dict:
        """
        Get current video settings.

        Returns video settings (resolution, FPS, etc.).
        """
        with obs_client() as client:
            result = client.get_video_settings()
            return {
                "fps_numerator": result.fps_numerator,
                "fps_denominator": result.fps_denominator,
                "base_width": result.base_width,
                "base_height": result.base_height,
                "output_width": result.output_width,
                "output_height": result.output_height,
            }

    @mcp.tool()
    def obs_set_video_settings(
        fps_numerator: int | None = None,
        fps_denominator: int | None = None,
        base_width: int | None = None,
        base_height: int | None = None,
        output_width: int | None = None,
        output_height: int | None = None,
    ) -> dict:
        """
        Set video settings.

        Args:
            fps_numerator: FPS numerator.
            fps_denominator: FPS denominator.
            base_width: Base (canvas) width.
            base_height: Base (canvas) height.
            output_width: Output (scaled) width.
            output_height: Output (scaled) height.

        Returns success status.
        """
        with obs_client() as client:
            client.set_video_settings(
                fps_numerator,
                fps_denominator,
                base_width,
                base_height,
                output_width,
                output_height,
            )
            return {"success": True}
