"""
Factory function for creating Resources instances based on configuration.

This module provides a factory function that selects the appropriate Resources
class based on configuration settings (platform, use_direct_access, use_graph_index).
"""
from __future__ import annotations
from typing import Union
from snowflake.snowpark import Session

from ...config import Config
from ...local import LocalResources
from . import Resources, DirectAccessResources, UseIndexResources
from ....tools.constants import USE_DIRECT_ACCESS, USE_GRAPH_INDEX, Generation


def create_resources_instance(
    config: Config | None = None,
    profile: str | None = None,
    dry_run: bool = False,
    connection: Session | None = None,
    reset_session: bool = False,
    language: str = "rel",
    generation: Generation = Generation.QB,
) -> Union[LocalResources, DirectAccessResources, UseIndexResources, Resources]:
    """
    Factory function that creates the appropriate Resources instance based on config.

    This function selects the Resources class based on:
    1. Platform (local -> LocalResources)
    2. use_direct_access flag (DirectAccessResources)
    3. use_graph_index flag (UseIndexResources)
    4. Default (base Resources)

    Args:
        config: Configuration object (optional, will create from profile if not provided)
        profile: Profile name (optional, used if config is not provided)
        dry_run: Whether to run in dry-run mode (default: False)
        connection: Optional Snowflake session connection
        reset_session: Whether to reset the session (default: False)
        language: Language for the resources instance (default: "rel")
        generation: Generation for the resources instance (default: Generation.QB)

    Returns:
        Appropriate Resources instance based on config settings:
        - LocalResources if platform is "local"
        - DirectAccessResources if use_direct_access is enabled
        - UseIndexResources if use_graph_index is enabled
        - Resources (base) otherwise
    """
    # Create config from profile if not provided
    if config is None:
        config = Config(profile)

    platform = config.get("platform", "")
    if platform == "local":
        return LocalResources(
            profile=profile,
            config=config,
            dry_run=dry_run,
            generation=generation,
            connection=connection,
            reset_session=reset_session,
            language=language,
        )

    if config.get("use_direct_access", USE_DIRECT_ACCESS):
        return DirectAccessResources(
            profile=profile,
            config=config,
            dry_run=dry_run,
            generation=generation,
            connection=connection,
            reset_session=reset_session,
            language=language,
        )

    if config.get("use_graph_index", USE_GRAPH_INDEX):
        return UseIndexResources(
            profile=profile,
            config=config,
            dry_run=dry_run,
            generation=generation,
            connection=connection,
            reset_session=reset_session,
            language=language,
        )

    return Resources(
        profile=profile,
        config=config,
        dry_run=dry_run,
        generation=generation,
        connection=connection,
        reset_session=reset_session,
        language=language,
    )


