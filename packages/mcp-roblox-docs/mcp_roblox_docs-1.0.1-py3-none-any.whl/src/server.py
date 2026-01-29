"""
MCP Roblox Docs - Main Server

A comprehensive MCP server for Roblox Studio documentation.
Provides always up-to-date API reference, search, and DevForum integration.

Usage:
    uv run src/server.py

Or via MCP config:
    {
        "command": "uv",
        "args": ["--directory", "/path/to/mcp-roblox-docs", "run", "src/server.py"]
    }
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import httpx
import platformdirs
from mcp.server.fastmcp import FastMCP

from src.data.loader import DataLoader
from src.data.syncer import DataSyncer, AVAILABLE_LANGUAGES
from src.data.index import SearchIndex
from src.utils.formatter import (
    format_class,
    format_enum,
    format_member,
    format_deprecation,
    format_search_results,
    format_inheritance,
    format_services,
)

# Configure logging to stderr (important for MCP!)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-roblox-docs")

# Cache directory - uses platform-appropriate user cache location
# Windows: C:\Users\<user>\AppData\Local\mcp-roblox-docs\
# Linux: ~/.cache/mcp-roblox-docs/
# macOS: ~/Library/Caches/mcp-roblox-docs/
CACHE_DIR = Path(platformdirs.user_cache_dir("mcp-roblox-docs"))

# Initialize FastMCP server
mcp = FastMCP("roblox-docs")

# Global state (initialized on startup)
_loader: DataLoader | None = None
_index: SearchIndex | None = None
_syncer: DataSyncer | None = None
_language: str = "en-us"


async def ensure_initialized() -> tuple[DataLoader, SearchIndex]:
    """Ensure data is loaded and index is built."""
    global _loader, _index, _syncer, _language

    if _loader is None:
        _syncer = DataSyncer(CACHE_DIR, language=_language)

        # Sync data if needed
        await _syncer.sync()

        _loader = DataLoader(CACHE_DIR, language=_language)

    if _index is None or not _index.is_built():
        _index = SearchIndex()

        # Build index
        classes = _loader.get_all_classes()
        enums = _loader.get_all_enums()
        docs = _loader.get_api_docs() or {}

        _index.build(classes, enums, docs)

    return _loader, _index


# ============================================================================
# CORE TOOLS
# ============================================================================


@mcp.tool()
async def roblox_search(query: str, limit: int = 25) -> str:
    """
    Search across all Roblox API - classes, members, enums.

    Use this to find APIs by name, functionality, or description.
    Supports partial matches and camelCase splitting.

    Args:
        query: Search query (e.g., "tween animation", "player character", "physics")
        limit: Maximum results to return (default 25, max 50)

    Returns:
        Formatted list of matching APIs with type, name, and description.
    """
    loader, index = await ensure_initialized()

    limit = min(max(1, limit), 50)
    results = index.search(query, limit=limit)

    return format_search_results(results, query)


@mcp.tool()
async def roblox_get_class(class_name: str, include_members: bool = True) -> str:
    """
    Get complete information about a Roblox class.

    Returns class description, inheritance, properties, methods, events, and callbacks.

    Args:
        class_name: Name of the class (e.g., "Part", "TweenService", "Player")
        include_members: Whether to include all members (default True)

    Returns:
        Formatted class information with all details.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found. Try using roblox_search to find the correct name."

    docs = loader.get_class_doc(class_name)

    return format_class(cls, docs, include_members=include_members)


@mcp.tool()
async def roblox_get_member(class_name: str, member_name: str) -> str:
    """
    Get detailed information about a specific class member.

    Works for properties, methods, events, and callbacks.

    Args:
        class_name: Name of the class (e.g., "Part", "TweenService")
        member_name: Name of the member (e.g., "Anchored", "Create", "Touched")

    Returns:
        Detailed member information including type, parameters, return values.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found."

    member = loader.get_member(class_name, member_name)
    if not member:
        # Try to find similar members
        all_members = loader.get_class_members(class_name)
        member_names = [m.get("Name", "") for m in all_members]

        # Simple fuzzy match
        suggestions = [n for n in member_names if member_name.lower() in n.lower()][:5]

        if suggestions:
            return f"Member '{member_name}' not found in {class_name}. Did you mean: {', '.join(suggestions)}?"
        return f"Member '{member_name}' not found in class '{class_name}'."

    docs = loader.get_class_doc(class_name)

    return format_member(member, class_name, docs)


@mcp.tool()
async def roblox_get_enum(enum_name: str) -> str:
    """
    Get all values of a Roblox enum.

    Useful for finding valid values for enum-typed properties.

    Args:
        enum_name: Name of the enum (e.g., "Material", "PartType", "EasingStyle")

    Returns:
        Enum name and all its values with their numeric codes.
    """
    loader, _ = await ensure_initialized()

    enum = loader.get_enum(enum_name)
    if not enum:
        # Try to find similar enums
        all_enums = loader.get_all_enums()
        enum_names = [e.get("Name", "") for e in all_enums]

        suggestions = [n for n in enum_names if enum_name.lower() in n.lower()][:5]

        if suggestions:
            return f"Enum '{enum_name}' not found. Did you mean: {', '.join(suggestions)}?"
        return f"Enum '{enum_name}' not found. Use roblox_search('enum <name>') to find enums."

    return format_enum(enum)


@mcp.tool()
async def roblox_check_deprecated(name: str, class_name: str | None = None) -> str:
    """
    Check if a class or member is deprecated.

    Provides deprecation status and suggests alternatives when available.

    Args:
        name: Name of the class or member to check
        class_name: If checking a member, provide the class name

    Returns:
        Deprecation status with alternatives if available.
    """
    loader, _ = await ensure_initialized()

    if class_name:
        # Check member
        member = loader.get_member(class_name, name)
        if not member:
            return f"Member '{name}' not found in class '{class_name}'."

        tags = member.get("Tags", [])
        is_deprecated = "Deprecated" in tags

        # Known deprecation mappings
        alternatives = get_deprecation_alternatives(name, class_name)

        return format_deprecation(
            name,
            is_class=False,
            is_deprecated=is_deprecated,
            class_name=class_name,
            tags=tags,
            alternatives=alternatives,
        )
    else:
        # Check class
        cls = loader.get_class(name)
        if not cls:
            return f"Class '{name}' not found."

        tags = cls.get("Tags", [])
        is_deprecated = "Deprecated" in tags

        alternatives = get_deprecation_alternatives(name, None)

        return format_deprecation(
            name, is_class=True, is_deprecated=is_deprecated, tags=tags, alternatives=alternatives
        )


# ============================================================================
# EXTENDED TOOLS
# ============================================================================


@mcp.tool()
async def roblox_list_services() -> str:
    """
    List all Roblox services.

    Services are singleton objects that provide core game functionality.
    Access them with game:GetService("ServiceName").

    Returns:
        List of all available services with their status.
    """
    loader, _ = await ensure_initialized()

    services = loader.get_services()

    return format_services(services)


@mcp.tool()
async def roblox_get_inheritance(class_name: str) -> str:
    """
    Get the inheritance hierarchy of a class.

    Shows the full ancestor chain and direct subclasses.

    Args:
        class_name: Name of the class (e.g., "Part", "BasePart", "Instance")

    Returns:
        Inheritance chain and list of direct subclasses.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found."

    chain = loader.get_inheritance(class_name)
    subclasses = loader.get_subclasses(class_name)

    return format_inheritance(class_name, chain, subclasses)


@mcp.tool()
async def roblox_search_devforum(query: str, limit: int = 10) -> str:
    """
    Search the Roblox Developer Forum for discussions and solutions.

    Great for finding best practices, tutorials, and community solutions.

    Args:
        query: Search query (e.g., "memory optimization", "pathfinding", "datastore")
        limit: Maximum results (default 10, max 25)

    Returns:
        List of relevant DevForum threads with titles and links.
    """
    limit = min(max(1, limit), 25)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://devforum.roblox.com/search.json",
                params={"q": query},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.warning(f"DevForum search failed: {e}")
        return f"DevForum search failed: {e}. Try again later or search directly at https://devforum.roblox.com"

    topics = data.get("topics", [])[:limit]

    if not topics:
        return f"No DevForum results for '{query}'. Try different keywords."

    lines = []
    lines.append(f"DevForum results for '{query}' ({len(topics)} found):")
    lines.append("")

    for i, topic in enumerate(topics, 1):
        title = topic.get("title", "Unknown")
        topic_id = topic.get("id", 0)
        category_id = topic.get("category_id", 0)

        # Determine category
        category = {
            4: "Help and Feedback",
            6: "Resources",
            10: "Scripting Support",
            11: "Building Support",
            12: "Art Design Support",
            45: "Code Review",
            55: "Community Tutorials",
        }.get(category_id, "Discussion")

        url = f"https://devforum.roblox.com/t/{topic_id}"

        lines.append(f"{i}. {title}")
        lines.append(f"   Category: {category}")
        lines.append(f"   Link: {url}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def roblox_recent_changes(days: int = 7) -> str:
    """
    Get information about recent API changes (placeholder).

    Note: This currently shows API version info. Full changelog tracking
    requires comparing historical API dumps.

    Args:
        days: Number of days to look back (currently unused)

    Returns:
        Current API version and available data sources.
    """
    loader, _ = await ensure_initialized()

    version = loader.get_version()

    lines = []
    lines.append("ROBLOX API VERSION INFO")
    lines.append("")
    lines.append(f"Current API Version: {version}")
    lines.append("")
    lines.append("Note: For detailed changelogs, see:")
    lines.append("  - https://github.com/MaximumADHD/Roblox-Client-Tracker")
    lines.append("  - https://devforum.roblox.com/c/updates/release-notes")
    lines.append("")
    lines.append("Use roblox_search_devforum('release notes') for recent updates.")

    return "\n".join(lines)


# ============================================================================
# UTILITY TOOLS
# ============================================================================


@mcp.tool()
async def roblox_sync(force: bool = False, language: str | None = None) -> str:
    """
    Force sync data from remote sources.

    Use this to update to the latest Roblox API data.

    Args:
        force: Force re-download even if data is current
        language: Switch documentation language (e.g., "en-us", "id-id", "ja-jp")

    Returns:
        Sync status and version information.
    """
    global _loader, _index, _syncer, _language

    # Update language if specified
    if language:
        if language not in AVAILABLE_LANGUAGES:
            return f"Unknown language: {language}. Available: {', '.join(AVAILABLE_LANGUAGES)}"
        _language = language

    # Clear caches
    if _loader:
        _loader.clear_cache()
    _index = None

    # Re-sync
    _syncer = DataSyncer(CACHE_DIR, language=_language)
    success = await _syncer.sync(force=force)

    # Reload
    _loader = DataLoader(CACHE_DIR, language=_language)

    if success:
        version = _loader.get_version()
        return f"Sync complete! API Version: {version}, Language: {_language}"
    else:
        return "Sync completed with some errors. Some data may be missing."


@mcp.tool()
async def roblox_list_enums(filter_text: str | None = None) -> str:
    """
    List all available Roblox enums.

    Args:
        filter_text: Optional filter to search enum names

    Returns:
        List of enum names (use roblox_get_enum for values).
    """
    loader, _ = await ensure_initialized()

    enums = loader.get_all_enums()

    if filter_text:
        filter_lower = filter_text.lower()
        enums = [e for e in enums if filter_lower in e.get("Name", "").lower()]

    if not enums:
        return f"No enums found matching '{filter_text}'" if filter_text else "No enums found."

    lines = []
    lines.append(f"ROBLOX ENUMS ({len(enums)} total)")
    lines.append("")

    for enum in sorted(enums, key=lambda e: e.get("Name", "")):
        name = enum.get("Name", "Unknown")
        item_count = len(enum.get("Items", []))
        lines.append(f"  {name} ({item_count} values)")

    lines.append("")
    lines.append("Use roblox_get_enum('EnumName') to see all values.")

    return "\n".join(lines)


# ============================================================================
# DEPRECATION ALTERNATIVES MAPPING
# ============================================================================


def get_deprecation_alternatives(name: str, class_name: str | None) -> list[str]:
    """Get known alternatives for deprecated APIs."""

    # Class-level deprecations
    class_alternatives = {
        "BodyPosition": ["AlignPosition (constraint-based)"],
        "BodyGyro": ["AlignOrientation (constraint-based)"],
        "BodyVelocity": ["LinearVelocity (constraint-based)"],
        "BodyForce": ["VectorForce (constraint-based)"],
        "BodyAngularVelocity": ["AngularVelocity (constraint-based)"],
        "BodyThrust": ["VectorForce (constraint-based)"],
        "RocketPropulsion": ["AlignPosition + AlignOrientation"],
        "Message": ["Use ScreenGui with TextLabel"],
        "Hint": ["Use ScreenGui with TextLabel"],
        "PointLight": ["Still works, but consider SurfaceLight or SpotLight"],
        "Sparkles": ["ParticleEmitter"],
        "Fire": ["ParticleEmitter"],
        "Smoke": ["ParticleEmitter"],
        "SelectionBox": ["Highlight"],
        "SelectionSphere": ["Highlight"],
    }

    # Member-level deprecations
    member_alternatives = {
        ("Instance", "IsA"): ["Use direct type checking or IsA with string"],
        ("Players", "LocalPlayer"): ["Still works - this is the correct way for client scripts"],
        ("Workspace", "FilteringEnabled"): ["Always enabled - remove this check"],
        ("BasePart", "Velocity"): ["AssemblyLinearVelocity"],
        ("BasePart", "RotVelocity"): ["AssemblyAngularVelocity"],
        ("Humanoid", "WalkSpeed"): ["Still works - use this for movement speed"],
        ("Model", "GetPrimaryPartCFrame"): ["Use Model.WorldPivot or PrimaryPart.CFrame"],
        ("Model", "SetPrimaryPartCFrame"): ["Use Model:PivotTo() or set WorldPivot"],
    }

    if class_name:
        return member_alternatives.get((class_name, name), [])
    else:
        return class_alternatives.get(name, [])


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP Roblox Docs server...")

    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
