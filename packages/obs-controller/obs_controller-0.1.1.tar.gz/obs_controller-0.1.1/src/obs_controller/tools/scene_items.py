"""Scene item (source positioning/visibility) tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register scene item tools."""

    @mcp.tool()
    def obs_list_scene_items(scene_name: str) -> dict:
        """
        Get list of scene items in a scene.

        Args:
            scene_name: Name of the scene.

        Returns list of scene items with their IDs, names, and types.
        """
        with obs_client() as client:
            result = client.get_scene_item_list(scene_name)
            return {
                "scene_name": scene_name,
                "scene_items": [
                    {
                        "scene_item_id": item["sceneItemId"],
                        "scene_item_index": item["sceneItemIndex"],
                        "scene_item_enabled": item["sceneItemEnabled"],
                        "scene_item_locked": item["sceneItemLocked"],
                        "source_name": item["sourceName"],
                        "source_type": item["sourceType"],
                        "source_uuid": item.get("sourceUuid"),
                        "input_kind": item.get("inputKind"),
                        "is_group": item.get("isGroup", False),
                    }
                    for item in result.scene_items
                ],
            }

    @mcp.tool()
    def obs_get_scene_item_id(scene_name: str, source_name: str) -> dict:
        """
        Get the scene item ID for a source in a scene.

        Args:
            scene_name: Name of the scene.
            source_name: Name of the source.

        Returns the scene item ID.
        """
        with obs_client() as client:
            result = client.get_scene_item_id(scene_name, source_name)
            return {
                "scene_name": scene_name,
                "source_name": source_name,
                "scene_item_id": result.scene_item_id,
            }

    @mcp.tool()
    def obs_get_scene_item_source(scene_name: str, scene_item_id: int) -> dict:
        """
        Get the source info for a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns source name and UUID.
        """
        with obs_client() as client:
            result = client.get_scene_item_source(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "source_name": result.source_name,
                "source_uuid": result.source_uuid,
            }

    @mcp.tool()
    def obs_create_scene_item(
        scene_name: str, source_name: str, enabled: bool = True
    ) -> dict:
        """
        Add an existing source to a scene as a new scene item.

        Args:
            scene_name: Name of the scene.
            source_name: Name of the source to add.
            enabled: Whether the scene item should be enabled.

        Returns the new scene item ID.
        """
        with obs_client() as client:
            result = client.create_scene_item(scene_name, source_name, enabled)
            return {
                "success": True,
                "scene_name": scene_name,
                "source_name": source_name,
                "scene_item_id": result.scene_item_id,
            }

    @mcp.tool()
    def obs_remove_scene_item(scene_name: str, scene_item_id: int) -> dict:
        """
        Remove a scene item from a scene.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item to remove.

        Returns success status.
        """
        with obs_client() as client:
            client.remove_scene_item(scene_name, scene_item_id)
            return {
                "success": True,
                "scene_name": scene_name,
                "removed_scene_item_id": scene_item_id,
            }

    @mcp.tool()
    def obs_duplicate_scene_item(
        scene_name: str,
        scene_item_id: int,
        destination_scene_name: str | None = None,
    ) -> dict:
        """
        Duplicate a scene item.

        Args:
            scene_name: Name of the scene containing the item.
            scene_item_id: ID of the scene item to duplicate.
            destination_scene_name: Optional scene to duplicate to (same scene if None).

        Returns the new scene item ID.
        """
        with obs_client() as client:
            result = client.duplicate_scene_item(
                scene_name, scene_item_id, destination_scene_name
            )
            return {
                "success": True,
                "source_scene": scene_name,
                "destination_scene": destination_scene_name or scene_name,
                "new_scene_item_id": result.scene_item_id,
            }

    @mcp.tool()
    def obs_get_scene_item_transform(scene_name: str, scene_item_id: int) -> dict:
        """
        Get transform/position of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns transform properties (position, rotation, scale, crop, etc.).
        """
        with obs_client() as client:
            result = client.get_scene_item_transform(scene_name, scene_item_id)
            transform = result.scene_item_transform
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "transform": {
                    "position_x": transform.get("positionX"),
                    "position_y": transform.get("positionY"),
                    "rotation": transform.get("rotation"),
                    "scale_x": transform.get("scaleX"),
                    "scale_y": transform.get("scaleY"),
                    "width": transform.get("width"),
                    "height": transform.get("height"),
                    "source_width": transform.get("sourceWidth"),
                    "source_height": transform.get("sourceHeight"),
                    "bounds_type": transform.get("boundsType"),
                    "bounds_width": transform.get("boundsWidth"),
                    "bounds_height": transform.get("boundsHeight"),
                    "bounds_alignment": transform.get("boundsAlignment"),
                    "crop_left": transform.get("cropLeft"),
                    "crop_right": transform.get("cropRight"),
                    "crop_top": transform.get("cropTop"),
                    "crop_bottom": transform.get("cropBottom"),
                    "alignment": transform.get("alignment"),
                },
            }

    @mcp.tool()
    def obs_set_scene_item_transform(
        scene_name: str, scene_item_id: int, transform: dict
    ) -> dict:
        """
        Set transform/position of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            transform: Transform properties to set. Can include:
                - positionX, positionY: Position in pixels
                - rotation: Rotation in degrees
                - scaleX, scaleY: Scale multipliers
                - boundsType: "OBS_BOUNDS_NONE", "OBS_BOUNDS_STRETCH", etc.
                - boundsWidth, boundsHeight: Bounds size
                - cropLeft, cropRight, cropTop, cropBottom: Crop in pixels
                - alignment: Alignment value (see OBS docs)

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_transform(scene_name, scene_item_id, transform)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
            }

    @mcp.tool()
    def obs_get_scene_item_enabled(scene_name: str, scene_item_id: int) -> dict:
        """
        Get visibility of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns enabled/visibility status.
        """
        with obs_client() as client:
            result = client.get_scene_item_enabled(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "enabled": result.scene_item_enabled,
            }

    @mcp.tool()
    def obs_set_scene_item_enabled(
        scene_name: str, scene_item_id: int, enabled: bool
    ) -> dict:
        """
        Set visibility of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            enabled: Whether to show (True) or hide (False) the item.

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_enabled(scene_name, scene_item_id, enabled)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "enabled": enabled,
            }

    @mcp.tool()
    def obs_get_scene_item_locked(scene_name: str, scene_item_id: int) -> dict:
        """
        Get locked status of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns locked status.
        """
        with obs_client() as client:
            result = client.get_scene_item_locked(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "locked": result.scene_item_locked,
            }

    @mcp.tool()
    def obs_set_scene_item_locked(
        scene_name: str, scene_item_id: int, locked: bool
    ) -> dict:
        """
        Set locked status of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            locked: Whether to lock (True) or unlock (False) the item.

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_locked(scene_name, scene_item_id, locked)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "locked": locked,
            }

    @mcp.tool()
    def obs_get_scene_item_index(scene_name: str, scene_item_id: int) -> dict:
        """
        Get the index (z-order) of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns the scene item index.
        """
        with obs_client() as client:
            result = client.get_scene_item_index(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "scene_item_index": result.scene_item_index,
            }

    @mcp.tool()
    def obs_set_scene_item_index(
        scene_name: str, scene_item_id: int, scene_item_index: int
    ) -> dict:
        """
        Set the index (z-order) of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            scene_item_index: New index for the item.

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_index(scene_name, scene_item_id, scene_item_index)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "scene_item_index": scene_item_index,
            }

    @mcp.tool()
    def obs_get_scene_item_blend_mode(scene_name: str, scene_item_id: int) -> dict:
        """
        Get the blend mode of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns the blend mode.
        """
        with obs_client() as client:
            result = client.get_scene_item_blend_mode(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "blend_mode": result.scene_item_blend_mode,
            }

    @mcp.tool()
    def obs_set_scene_item_blend_mode(
        scene_name: str, scene_item_id: int, blend_mode: str
    ) -> dict:
        """
        Set the blend mode of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            blend_mode: Blend mode (OBS_BLEND_NORMAL, OBS_BLEND_ADDITIVE,
                       OBS_BLEND_SUBTRACT, OBS_BLEND_SCREEN, OBS_BLEND_MULTIPLY,
                       OBS_BLEND_LIGHTEN, OBS_BLEND_DARKEN).

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_blend_mode(scene_name, scene_item_id, blend_mode)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "blend_mode": blend_mode,
            }

    @mcp.tool()
    def obs_get_scene_item_private_settings(scene_name: str, scene_item_id: int) -> dict:
        """
        Get private settings of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.

        Returns private settings.
        """
        with obs_client() as client:
            result = client.get_scene_item_private_settings(scene_name, scene_item_id)
            return {
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
                "private_settings": result.scene_item_private_settings,
            }

    @mcp.tool()
    def obs_set_scene_item_private_settings(
        scene_name: str, scene_item_id: int, settings: dict
    ) -> dict:
        """
        Set private settings of a scene item.

        Args:
            scene_name: Name of the scene.
            scene_item_id: ID of the scene item.
            settings: Private settings to set.

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_item_private_settings(scene_name, scene_item_id, settings)
            return {
                "success": True,
                "scene_name": scene_name,
                "scene_item_id": scene_item_id,
            }
