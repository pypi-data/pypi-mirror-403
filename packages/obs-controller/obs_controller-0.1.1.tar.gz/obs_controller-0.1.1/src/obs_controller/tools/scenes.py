"""Scene management tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register scene management tools."""

    @mcp.tool()
    def obs_list_scenes() -> dict:
        """
        List all scenes in OBS.

        Returns list of scene names and the current program/preview scenes.
        """
        with obs_client() as client:
            scenes = client.get_scene_list()
            return {
                "current_program_scene": scenes.current_program_scene_name,
                "current_preview_scene": scenes.current_preview_scene_name,
                "scenes": [
                    {"name": s["sceneName"], "index": s["sceneIndex"]}
                    for s in scenes.scenes
                ],
            }

    @mcp.tool()
    def obs_get_current_program_scene() -> dict:
        """
        Get the current program (active) scene.

        Returns the name of the currently active scene.
        """
        with obs_client() as client:
            scene = client.get_current_program_scene()
            return {
                "current_program_scene": scene.current_program_scene_name,
                "scene_uuid": scene.current_program_scene_uuid,
            }

    @mcp.tool()
    def obs_set_current_program_scene(scene_name: str) -> dict:
        """
        Set the current program (active) scene.

        Args:
            scene_name: Name of the scene to switch to.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_program_scene(scene_name)
            return {"success": True, "switched_to": scene_name}

    @mcp.tool()
    def obs_get_current_preview_scene() -> dict:
        """
        Get the current preview scene (studio mode only).

        Returns the name of the current preview scene.
        """
        with obs_client() as client:
            scene = client.get_current_preview_scene()
            return {
                "current_preview_scene": scene.current_preview_scene_name,
                "scene_uuid": scene.current_preview_scene_uuid,
            }

    @mcp.tool()
    def obs_set_current_preview_scene(scene_name: str) -> dict:
        """
        Set the current preview scene (studio mode only).

        Args:
            scene_name: Name of the scene to set as preview.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_preview_scene(scene_name)
            return {"success": True, "preview_scene": scene_name}

    @mcp.tool()
    def obs_create_scene(scene_name: str) -> dict:
        """
        Create a new scene.

        Args:
            scene_name: Name for the new scene.

        Returns the UUID of the created scene.
        """
        with obs_client() as client:
            result = client.create_scene(scene_name)
            return {"success": True, "scene_name": scene_name, "scene_uuid": result.scene_uuid}

    @mcp.tool()
    def obs_remove_scene(scene_name: str) -> dict:
        """
        Remove a scene.

        Args:
            scene_name: Name of the scene to remove.

        Returns success status.
        """
        with obs_client() as client:
            client.remove_scene(scene_name)
            return {"success": True, "removed_scene": scene_name}

    @mcp.tool()
    def obs_set_scene_name(scene_name: str, new_name: str) -> dict:
        """
        Rename a scene.

        Args:
            scene_name: Current name of the scene.
            new_name: New name for the scene.

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_name(scene_name, new_name)
            return {"success": True, "old_name": scene_name, "new_name": new_name}

    @mcp.tool()
    def obs_get_scene_scene_transition_override(scene_name: str) -> dict:
        """
        Get the scene transition override for a scene.

        Args:
            scene_name: Name of the scene.

        Returns transition override details.
        """
        with obs_client() as client:
            result = client.get_scene_scene_transition_override(scene_name)
            return {
                "scene_name": scene_name,
                "transition_name": result.transition_name,
                "transition_duration": result.transition_duration,
            }

    @mcp.tool()
    def obs_set_scene_scene_transition_override(
        scene_name: str,
        transition_name: str | None = None,
        transition_duration: int | None = None,
    ) -> dict:
        """
        Set the scene transition override for a scene.

        Args:
            scene_name: Name of the scene.
            transition_name: Name of transition to use (None to remove override).
            transition_duration: Duration in milliseconds (None to use default).

        Returns success status.
        """
        with obs_client() as client:
            client.set_scene_scene_transition_override(
                scene_name, transition_name, transition_duration
            )
            return {
                "success": True,
                "scene_name": scene_name,
                "transition_name": transition_name,
                "transition_duration": transition_duration,
            }

    @mcp.tool()
    def obs_get_group_list() -> dict:
        """
        Get list of all groups in OBS.

        Returns list of group names.
        """
        with obs_client() as client:
            groups = client.get_group_list()
            return {"groups": groups.groups}

    @mcp.tool()
    def obs_get_group_scene_item_list(scene_name: str) -> dict:
        """
        Get list of scene items in a group.

        Args:
            scene_name: Name of the group.

        Returns list of scene items in the group.
        """
        with obs_client() as client:
            result = client.get_group_scene_item_list(scene_name)
            return {
                "group_name": scene_name,
                "scene_items": [
                    {
                        "scene_item_id": item["sceneItemId"],
                        "scene_item_index": item["sceneItemIndex"],
                        "source_name": item["sourceName"],
                        "source_type": item["sourceType"],
                        "source_uuid": item.get("sourceUuid"),
                        "input_kind": item.get("inputKind"),
                        "is_group": item.get("isGroup", False),
                    }
                    for item in result.scene_items
                ],
            }
