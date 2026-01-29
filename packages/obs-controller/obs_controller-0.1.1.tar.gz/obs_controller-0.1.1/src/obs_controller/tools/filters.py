"""Source filter tools."""

from fastmcp import FastMCP

from ..client import obs_client


def register_tools(mcp: FastMCP):
    """Register source filter tools."""

    @mcp.tool()
    def obs_get_source_filter_kind_list() -> dict:
        """
        Get list of available source filter kinds.

        Returns list of filter kind names.
        """
        with obs_client() as client:
            result = client.get_source_filter_kind_list()
            return {"filter_kinds": result.source_filter_kinds}

    @mcp.tool()
    def obs_list_source_filters(source_name: str) -> dict:
        """
        Get list of filters on a source.

        Args:
            source_name: Name of the source.

        Returns list of filters with their settings.
        """
        with obs_client() as client:
            result = client.get_source_filter_list(source_name)
            return {
                "source_name": source_name,
                "filters": [
                    {
                        "name": f["filterName"],
                        "kind": f["filterKind"],
                        "index": f["filterIndex"],
                        "enabled": f["filterEnabled"],
                        "settings": f["filterSettings"],
                    }
                    for f in result.filters
                ],
            }

    @mcp.tool()
    def obs_get_source_filter_default_settings(filter_kind: str) -> dict:
        """
        Get default settings for a filter kind.

        Args:
            filter_kind: The kind of filter.

        Returns default settings for the filter kind.
        """
        with obs_client() as client:
            result = client.get_source_filter_default_settings(filter_kind)
            return {
                "filter_kind": filter_kind,
                "default_settings": result.default_filter_settings,
            }

    @mcp.tool()
    def obs_create_source_filter(
        source_name: str,
        filter_name: str,
        filter_kind: str,
        filter_settings: dict | None = None,
    ) -> dict:
        """
        Create a new filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Name for the new filter.
            filter_kind: Kind of filter to create.
            filter_settings: Optional filter settings.

        Returns success status.
        """
        with obs_client() as client:
            client.create_source_filter(
                source_name, filter_name, filter_kind, filter_settings or {}
            )
            return {
                "success": True,
                "source_name": source_name,
                "filter_name": filter_name,
                "filter_kind": filter_kind,
            }

    @mcp.tool()
    def obs_remove_source_filter(source_name: str, filter_name: str) -> dict:
        """
        Remove a filter from a source.

        Args:
            source_name: Name of the source.
            filter_name: Name of the filter to remove.

        Returns success status.
        """
        with obs_client() as client:
            client.remove_source_filter(source_name, filter_name)
            return {
                "success": True,
                "source_name": source_name,
                "removed_filter": filter_name,
            }

    @mcp.tool()
    def obs_set_source_filter_name(
        source_name: str, filter_name: str, new_name: str
    ) -> dict:
        """
        Rename a filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Current name of the filter.
            new_name: New name for the filter.

        Returns success status.
        """
        with obs_client() as client:
            client.set_source_filter_name(source_name, filter_name, new_name)
            return {
                "success": True,
                "source_name": source_name,
                "old_name": filter_name,
                "new_name": new_name,
            }

    @mcp.tool()
    def obs_get_source_filter(source_name: str, filter_name: str) -> dict:
        """
        Get details of a specific filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Name of the filter.

        Returns filter details and settings.
        """
        with obs_client() as client:
            result = client.get_source_filter(source_name, filter_name)
            return {
                "source_name": source_name,
                "filter_name": filter_name,
                "filter_enabled": result.filter_enabled,
                "filter_index": result.filter_index,
                "filter_kind": result.filter_kind,
                "filter_settings": result.filter_settings,
            }

    @mcp.tool()
    def obs_set_source_filter_index(
        source_name: str, filter_name: str, filter_index: int
    ) -> dict:
        """
        Set the index (order) of a filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Name of the filter.
            filter_index: New index for the filter.

        Returns success status.
        """
        with obs_client() as client:
            client.set_source_filter_index(source_name, filter_name, filter_index)
            return {
                "success": True,
                "source_name": source_name,
                "filter_name": filter_name,
                "filter_index": filter_index,
            }

    @mcp.tool()
    def obs_set_source_filter_settings(
        source_name: str, filter_name: str, settings: dict, overlay: bool = True
    ) -> dict:
        """
        Set settings for a filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Name of the filter.
            settings: Settings to apply.
            overlay: If True, overlay on existing; if False, replace.

        Returns success status.
        """
        with obs_client() as client:
            client.set_source_filter_settings(source_name, filter_name, settings, overlay)
            return {
                "success": True,
                "source_name": source_name,
                "filter_name": filter_name,
                "overlay": overlay,
            }

    @mcp.tool()
    def obs_set_source_filter_enabled(
        source_name: str, filter_name: str, enabled: bool
    ) -> dict:
        """
        Enable or disable a filter on a source.

        Args:
            source_name: Name of the source.
            filter_name: Name of the filter.
            enabled: Whether to enable (True) or disable (False).

        Returns success status.
        """
        with obs_client() as client:
            client.set_source_filter_enabled(source_name, filter_name, enabled)
            return {
                "success": True,
                "source_name": source_name,
                "filter_name": filter_name,
                "enabled": enabled,
            }
