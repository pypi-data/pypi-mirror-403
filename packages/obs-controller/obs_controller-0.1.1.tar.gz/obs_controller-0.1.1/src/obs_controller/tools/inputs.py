"""Input and audio control tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register input/audio control tools."""

    @mcp.tool()
    def obs_list_inputs(input_kind: str | None = None) -> dict:
        """
        List all inputs in OBS.

        Args:
            input_kind: Optional filter by input kind (e.g., "wasapi_input_capture").

        Returns list of inputs with their kinds.
        """
        with obs_client() as client:
            inputs = client.get_input_list(input_kind)
            return {
                "inputs": [
                    {
                        "name": i["inputName"],
                        "kind": i["inputKind"],
                        "unversioned_kind": i["unversionedInputKind"],
                        "uuid": i.get("inputUuid"),
                    }
                    for i in inputs.inputs
                ]
            }

    @mcp.tool()
    def obs_get_input_kind_list(unversioned: bool = False) -> dict:
        """
        Get list of available input kinds.

        Args:
            unversioned: Whether to return unversioned kinds.

        Returns list of input kinds.
        """
        with obs_client() as client:
            kinds = client.get_input_kind_list(unversioned)
            return {"input_kinds": kinds.input_kinds}

    @mcp.tool()
    def obs_get_special_inputs() -> dict:
        """
        Get names of special inputs (desktop audio, mic, etc.).

        Returns names of special system inputs.
        """
        with obs_client() as client:
            inputs = client.get_special_inputs()
            return {
                "desktop_1": inputs.desktop_1,
                "desktop_2": inputs.desktop_2,
                "mic_1": inputs.mic_1,
                "mic_2": inputs.mic_2,
                "mic_3": inputs.mic_3,
                "mic_4": inputs.mic_4,
            }

    @mcp.tool()
    def obs_create_input(
        scene_name: str,
        input_name: str,
        input_kind: str,
        input_settings: dict | None = None,
        scene_item_enabled: bool = True,
    ) -> dict:
        """
        Create a new input and add it to a scene.

        Args:
            scene_name: Name of scene to add input to.
            input_name: Name for the new input.
            input_kind: Kind of input to create.
            input_settings: Optional settings for the input.
            scene_item_enabled: Whether the scene item is enabled.

        Returns the created input's scene item ID and UUID.
        """
        with obs_client() as client:
            result = client.create_input(
                scene_name,
                input_name,
                input_kind,
                input_settings or {},
                scene_item_enabled,
            )
            return {
                "success": True,
                "input_name": input_name,
                "input_uuid": result.input_uuid,
                "scene_item_id": result.scene_item_id,
            }

    @mcp.tool()
    def obs_remove_input(input_name: str) -> dict:
        """
        Remove an input.

        Args:
            input_name: Name of the input to remove.

        Returns success status.
        """
        with obs_client() as client:
            client.remove_input(input_name)
            return {"success": True, "removed_input": input_name}

    @mcp.tool()
    def obs_set_input_name(input_name: str, new_name: str) -> dict:
        """
        Rename an input.

        Args:
            input_name: Current name of the input.
            new_name: New name for the input.

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_name(input_name, new_name)
            return {"success": True, "old_name": input_name, "new_name": new_name}

    @mcp.tool()
    def obs_get_input_default_settings(input_kind: str) -> dict:
        """
        Get default settings for an input kind.

        Args:
            input_kind: The input kind to get defaults for.

        Returns default settings.
        """
        with obs_client() as client:
            result = client.get_input_default_settings(input_kind)
            return {
                "input_kind": input_kind,
                "default_settings": result.default_input_settings,
            }

    @mcp.tool()
    def obs_get_input_settings(input_name: str) -> dict:
        """
        Get current settings for an input.

        Args:
            input_name: Name of the input.

        Returns current input settings.
        """
        with obs_client() as client:
            result = client.get_input_settings(input_name)
            return {
                "input_name": input_name,
                "input_kind": result.input_kind,
                "input_settings": result.input_settings,
            }

    @mcp.tool()
    def obs_set_input_settings(
        input_name: str, input_settings: dict, overlay: bool = True
    ) -> dict:
        """
        Set settings for an input.

        Args:
            input_name: Name of the input.
            input_settings: Settings to apply.
            overlay: If True, overlay on existing settings; if False, replace all.

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_settings(input_name, input_settings, overlay)
            return {
                "success": True,
                "input_name": input_name,
                "overlay": overlay,
            }

    @mcp.tool()
    def obs_get_input_mute(input_name: str) -> dict:
        """
        Get mute status of an input.

        Args:
            input_name: Name of the input.

        Returns mute status.
        """
        with obs_client() as client:
            result = client.get_input_mute(input_name)
            return {
                "input_name": input_name,
                "muted": result.input_muted,
            }

    @mcp.tool()
    def obs_set_input_mute(input_name: str, muted: bool) -> dict:
        """
        Set mute status of an input.

        Args:
            input_name: Name of the input.
            muted: Whether to mute (True) or unmute (False).

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_mute(input_name, muted)
            return {
                "success": True,
                "input_name": input_name,
                "muted": muted,
            }

    @mcp.tool()
    def obs_toggle_input_mute(input_name: str) -> dict:
        """
        Toggle mute status of an input.

        Args:
            input_name: Name of the input.

        Returns new mute status.
        """
        with obs_client() as client:
            result = client.toggle_input_mute(input_name)
            return {
                "input_name": input_name,
                "muted": result.input_muted,
            }

    @mcp.tool()
    def obs_get_input_volume(input_name: str) -> dict:
        """
        Get volume of an input.

        Args:
            input_name: Name of the input.

        Returns volume in dB and multiplier.
        """
        with obs_client() as client:
            result = client.get_input_volume(input_name)
            return {
                "input_name": input_name,
                "volume_db": result.input_volume_db,
                "volume_mul": result.input_volume_mul,
            }

    @mcp.tool()
    def obs_set_input_volume(
        input_name: str, volume_db: float | None = None, volume_mul: float | None = None
    ) -> dict:
        """
        Set volume of an input.

        Args:
            input_name: Name of the input.
            volume_db: Volume in dB (-inf to 26). Use this OR volume_mul.
            volume_mul: Volume multiplier (0 to ~9.943). Use this OR volume_db.

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_volume(input_name, vol_db=volume_db, vol_mul=volume_mul)
            return {
                "success": True,
                "input_name": input_name,
                "volume_db": volume_db,
                "volume_mul": volume_mul,
            }

    @mcp.tool()
    def obs_get_input_audio_balance(input_name: str) -> dict:
        """
        Get audio balance of an input.

        Args:
            input_name: Name of the input.

        Returns audio balance (0.0 = left, 0.5 = center, 1.0 = right).
        """
        with obs_client() as client:
            result = client.get_input_audio_balance(input_name)
            return {
                "input_name": input_name,
                "audio_balance": result.input_audio_balance,
            }

    @mcp.tool()
    def obs_set_input_audio_balance(input_name: str, balance: float) -> dict:
        """
        Set audio balance of an input.

        Args:
            input_name: Name of the input.
            balance: Balance value (0.0 = left, 0.5 = center, 1.0 = right).

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_audio_balance(input_name, balance)
            return {
                "success": True,
                "input_name": input_name,
                "audio_balance": balance,
            }

    @mcp.tool()
    def obs_get_input_audio_sync_offset(input_name: str) -> dict:
        """
        Get audio sync offset of an input.

        Args:
            input_name: Name of the input.

        Returns sync offset in milliseconds.
        """
        with obs_client() as client:
            result = client.get_input_audio_sync_offset(input_name)
            return {
                "input_name": input_name,
                "sync_offset_ms": result.input_audio_sync_offset,
            }

    @mcp.tool()
    def obs_set_input_audio_sync_offset(input_name: str, offset_ms: int) -> dict:
        """
        Set audio sync offset of an input.

        Args:
            input_name: Name of the input.
            offset_ms: Sync offset in milliseconds (-950 to 20000).

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_audio_sync_offset(input_name, offset_ms)
            return {
                "success": True,
                "input_name": input_name,
                "sync_offset_ms": offset_ms,
            }

    @mcp.tool()
    def obs_get_input_audio_monitor_type(input_name: str) -> dict:
        """
        Get audio monitor type of an input.

        Args:
            input_name: Name of the input.

        Returns monitor type.
        """
        with obs_client() as client:
            result = client.get_input_audio_monitor_type(input_name)
            return {
                "input_name": input_name,
                "monitor_type": result.monitor_type,
            }

    @mcp.tool()
    def obs_set_input_audio_monitor_type(input_name: str, monitor_type: str) -> dict:
        """
        Set audio monitor type of an input.

        Args:
            input_name: Name of the input.
            monitor_type: Monitor type (OBS_MONITORING_TYPE_NONE,
                         OBS_MONITORING_TYPE_MONITOR_ONLY,
                         OBS_MONITORING_TYPE_MONITOR_AND_OUTPUT).

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_audio_monitor_type(input_name, monitor_type)
            return {
                "success": True,
                "input_name": input_name,
                "monitor_type": monitor_type,
            }

    @mcp.tool()
    def obs_get_input_audio_tracks(input_name: str) -> dict:
        """
        Get audio tracks configuration for an input.

        Args:
            input_name: Name of the input.

        Returns audio tracks configuration.
        """
        with obs_client() as client:
            result = client.get_input_audio_tracks(input_name)
            return {
                "input_name": input_name,
                "audio_tracks": result.input_audio_tracks,
            }

    @mcp.tool()
    def obs_set_input_audio_tracks(input_name: str, audio_tracks: dict) -> dict:
        """
        Set audio tracks configuration for an input.

        Args:
            input_name: Name of the input.
            audio_tracks: Dict of track numbers to enabled status (e.g., {"1": True, "2": False}).

        Returns success status.
        """
        with obs_client() as client:
            client.set_input_audio_tracks(input_name, audio_tracks)
            return {
                "success": True,
                "input_name": input_name,
                "audio_tracks": audio_tracks,
            }

    @mcp.tool()
    def obs_get_input_properties_list_property_items(
        input_name: str, property_name: str
    ) -> dict:
        """
        Get list of items for a list property on an input.

        Args:
            input_name: Name of the input.
            property_name: Name of the list property.

        Returns list of property items.
        """
        with obs_client() as client:
            result = client.get_input_properties_list_property_items(
                input_name, property_name
            )
            return {
                "input_name": input_name,
                "property_name": property_name,
                "property_items": result.property_items,
            }

    @mcp.tool()
    def obs_press_input_properties_button(input_name: str, property_name: str) -> dict:
        """
        Press a button property on an input's properties.

        Args:
            input_name: Name of the input.
            property_name: Name of the button property.

        Returns success status.
        """
        with obs_client() as client:
            client.press_input_properties_button(input_name, property_name)
            return {
                "success": True,
                "input_name": input_name,
                "property_name": property_name,
            }
