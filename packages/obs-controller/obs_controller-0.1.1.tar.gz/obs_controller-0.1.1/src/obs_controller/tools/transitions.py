"""Scene transition tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register transition control tools."""

    @mcp.tool()
    def obs_list_transitions() -> dict:
        """
        Get list of available scene transitions.

        Returns list of transitions and the current transition.
        """
        with obs_client() as client:
            result = client.get_scene_transition_list()
            return {
                "current_transition": result.current_scene_transition_name,
                "current_transition_kind": result.current_scene_transition_kind,
                "current_transition_uuid": result.current_scene_transition_uuid,
                "transitions": [
                    {
                        "name": t["transitionName"],
                        "kind": t["transitionKind"],
                        "fixed": t["transitionFixed"],
                        "configurable": t["transitionConfigurable"],
                        "uuid": t.get("transitionUuid"),
                    }
                    for t in result.transitions
                ],
            }

    @mcp.tool()
    def obs_get_transition_kind_list() -> dict:
        """
        Get list of available transition kinds.

        Returns list of transition kind names.
        """
        with obs_client() as client:
            result = client.get_transition_kind_list()
            return {"transition_kinds": result.transition_kinds}

    @mcp.tool()
    def obs_get_current_scene_transition() -> dict:
        """
        Get the current scene transition.

        Returns current transition name, kind, duration, and settings.
        """
        with obs_client() as client:
            result = client.get_current_scene_transition()
            return {
                "transition_name": result.transition_name,
                "transition_kind": result.transition_kind,
                "transition_uuid": result.transition_uuid,
                "transition_fixed": result.transition_fixed,
                "transition_duration": result.transition_duration,
                "transition_configurable": result.transition_configurable,
                "transition_settings": result.transition_settings,
            }

    @mcp.tool()
    def obs_set_current_scene_transition(transition_name: str) -> dict:
        """
        Set the current scene transition.

        Args:
            transition_name: Name of the transition to use.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_scene_transition(transition_name)
            return {
                "success": True,
                "transition_name": transition_name,
            }

    @mcp.tool()
    def obs_set_current_scene_transition_duration(duration_ms: int) -> dict:
        """
        Set the duration of the current scene transition.

        Args:
            duration_ms: Duration in milliseconds.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_scene_transition_duration(duration_ms)
            return {
                "success": True,
                "transition_duration": duration_ms,
            }

    @mcp.tool()
    def obs_set_current_scene_transition_settings(
        settings: dict, overlay: bool = True
    ) -> dict:
        """
        Set settings for the current scene transition.

        Args:
            settings: Settings to apply.
            overlay: If True, overlay on existing settings; if False, replace.

        Returns success status.
        """
        with obs_client() as client:
            client.set_current_scene_transition_settings(settings, overlay)
            return {
                "success": True,
                "overlay": overlay,
            }

    @mcp.tool()
    def obs_get_current_scene_transition_cursor() -> dict:
        """
        Get the cursor position of the current scene transition.

        Returns cursor position (0.0 to 1.0).
        """
        with obs_client() as client:
            result = client.get_current_scene_transition_cursor()
            return {
                "transition_cursor": result.transition_cursor,
            }

    @mcp.tool()
    def obs_trigger_studio_mode_transition() -> dict:
        """
        Trigger the scene transition in studio mode.

        Transitions from preview to program.

        Returns success status.
        """
        with obs_client() as client:
            client.trigger_studio_mode_transition()
            return {
                "success": True,
                "message": "Studio mode transition triggered",
            }

    @mcp.tool()
    def obs_set_tbar_position(position: float) -> dict:
        """
        Set the T-Bar position (manual transition control).

        Args:
            position: Position from 0.0 to 1.0.

        Returns success status.
        """
        with obs_client() as client:
            client.set_t_bar_position(position)
            return {
                "success": True,
                "position": position,
            }
